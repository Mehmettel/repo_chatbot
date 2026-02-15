"""
Hybrid Search - Vektör + Full-text arama birleşimi.
V2: Semantik benzerlik + keyword eşleşme ile daha doğru sonuçlar.
"""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.intelligence.vectorizer import get_embedding


# Hybrid search ağırlıkları
VECTOR_WEIGHT = 0.7  # Semantik benzerlik ağırlığı
FTS_WEIGHT = 0.3     # Full-text search ağırlığı


async def vector_search(
    db: AsyncSession,
    query_text: str,
    folder_ids: list[UUID],
    folder_id: UUID | None = None,
    limit: int = 10,
    min_score: float | None = 0.0,
) -> list[tuple[UUID, str | None, str | None, float]]:
    """
    Metin sorgusunu vektöre çevirip pgvector ile en yakın videoları döner.
    Returns: list of (video_id, s3_key, description_ai, score).
    """
    if not folder_ids:
        return []
    vec = get_embedding(query_text)
    vec_str = "[" + ",".join(str(x) for x in vec) + "]"
    folder_list = ",".join(f"'{f}'" for f in folder_ids)
    folder_filter = f"AND folder_id IN ({folder_list})"
    if folder_id is not None:
        folder_filter += f" AND folder_id = '{folder_id}'"
    
    # pgvector: <=> cosine distance operator
    sql = text(f"""
        SELECT id, s3_key, description_ai,
               1 - (embedding <=> '{vec_str}'::vector) AS score
        FROM videos
        WHERE embedding IS NOT NULL
        {folder_filter}
        ORDER BY embedding <=> '{vec_str}'::vector
        LIMIT {limit}
    """)
    result = await db.execute(sql)
    rows = result.fetchall()
    out = []
    for row in rows:
        vid, s3_key, desc_ai, score = row[0], row[1], row[2], float(row[3]) if row[3] is not None else 0.0
        if min_score is not None and score < min_score:
            continue
        out.append((vid, s3_key, desc_ai, score))
    return out


async def hybrid_search(
    db: AsyncSession,
    query_text: str,
    folder_ids: list[UUID],
    folder_id: UUID | None = None,
    limit: int = 10,
    min_score: float | None = 0.0,
    vector_weight: float = VECTOR_WEIGHT,
    fts_weight: float = FTS_WEIGHT,
) -> list[tuple[UUID, str | None, str | None, str | None, float, float, float]]:
    """
    Hybrid search: Vektör araması + Full-text search birleşimi.
    
    Returns: list of (video_id, s3_key, title, description_ai, hybrid_score, vector_score, fts_score).
    
    Hybrid skor = (vector_weight * vector_score) + (fts_weight * fts_score)
    """
    if not folder_ids:
        return []
    
    # Embedding oluştur
    vec = get_embedding(query_text)
    vec_str = "[" + ",".join(str(x) for x in vec) + "]"
    
    # Folder filter
    folder_list = ",".join(f"'{f}'" for f in folder_ids)
    folder_filter = f"folder_id IN ({folder_list})"
    if folder_id is not None:
        folder_filter += f" AND folder_id = '{folder_id}'"
    
    # Full-text search query'si - Türkçe için simple config kullan
    # plainto_tsquery daha toleranslı, websearch_to_tsquery daha gelişmiş
    fts_query = query_text.replace("'", "''")  # SQL injection koruması
    
    # Hybrid SQL sorgusu
    # Vector score: 1 - cosine_distance (0-1 arası, 1 = tam eşleşme)
    # FTS score: ts_rank_cd (0-1 arası normalize edilmiş)
    sql = text(f"""
        WITH vector_results AS (
            SELECT 
                id,
                s3_key,
                title,
                description_ai,
                1 - (embedding <=> '{vec_str}'::vector) AS vector_score
            FROM videos
            WHERE embedding IS NOT NULL
            AND {folder_filter}
        ),
        fts_results AS (
            SELECT 
                id,
                CASE 
                    WHEN search_vector IS NOT NULL 
                    THEN ts_rank_cd(search_vector, plainto_tsquery('pg_catalog.simple', '{fts_query}'))
                    ELSE 0.0
                END AS fts_score
            FROM videos
            WHERE {folder_filter}
        )
        SELECT 
            v.id,
            v.s3_key,
            v.title,
            v.description_ai,
            ({vector_weight} * v.vector_score + {fts_weight} * COALESCE(f.fts_score, 0)) AS hybrid_score,
            v.vector_score,
            COALESCE(f.fts_score, 0) AS fts_score
        FROM vector_results v
        LEFT JOIN fts_results f ON v.id = f.id
        ORDER BY hybrid_score DESC
        LIMIT {limit}
    """)
    
    result = await db.execute(sql)
    rows = result.fetchall()
    
    out = []
    for row in rows:
        vid = row[0]
        s3_key = row[1]
        title = row[2]
        desc_ai = row[3]
        hybrid_score = float(row[4]) if row[4] is not None else 0.0
        vector_score = float(row[5]) if row[5] is not None else 0.0
        fts_score = float(row[6]) if row[6] is not None else 0.0
        
        if min_score is not None and hybrid_score < min_score:
            continue
        
        out.append((vid, s3_key, title, desc_ai, hybrid_score, vector_score, fts_score))
    
    return out


async def keyword_boost_search(
    db: AsyncSession,
    query_text: str,
    folder_ids: list[UUID],
    folder_id: UUID | None = None,
    limit: int = 10,
    min_score: float | None = 0.0,
) -> list[tuple[UUID, str | None, str | None, str | None, float]]:
    """
    Vektör araması + keyword boost.
    Başlıkta veya açıklamada sorgu kelimeleri geçiyorsa skoru artır.
    
    Returns: list of (video_id, s3_key, title, description_ai, boosted_score).
    """
    if not folder_ids:
        return []
    
    vec = get_embedding(query_text)
    vec_str = "[" + ",".join(str(x) for x in vec) + "]"
    
    folder_list = ",".join(f"'{f}'" for f in folder_ids)
    folder_filter = f"folder_id IN ({folder_list})"
    if folder_id is not None:
        folder_filter += f" AND folder_id = '{folder_id}'"
    
    # Sorgu kelimelerini ayır (boost için)
    query_words = [w.strip().lower() for w in query_text.split() if len(w.strip()) > 2]
    
    # ILIKE ile keyword boost
    keyword_boost_cases = []
    for word in query_words[:5]:  # Max 5 kelime
        safe_word = word.replace("'", "''")
        keyword_boost_cases.append(
            f"CASE WHEN LOWER(COALESCE(title, '')) LIKE '%{safe_word}%' THEN 0.1 ELSE 0 END"
        )
        keyword_boost_cases.append(
            f"CASE WHEN LOWER(COALESCE(description_ai, '')) LIKE '%{safe_word}%' THEN 0.05 ELSE 0 END"
        )
    
    boost_expr = " + ".join(keyword_boost_cases) if keyword_boost_cases else "0"
    
    sql = text(f"""
        SELECT 
            id,
            s3_key,
            title,
            description_ai,
            (1 - (embedding <=> '{vec_str}'::vector)) + ({boost_expr}) AS boosted_score
        FROM videos
        WHERE embedding IS NOT NULL
        AND {folder_filter}
        ORDER BY boosted_score DESC
        LIMIT {limit}
    """)
    
    result = await db.execute(sql)
    rows = result.fetchall()
    
    out = []
    for row in rows:
        vid = row[0]
        s3_key = row[1]
        title = row[2]
        desc_ai = row[3]
        score = float(row[4]) if row[4] is not None else 0.0
        
        if min_score is not None and score < min_score:
            continue
        
        out.append((vid, s3_key, title, desc_ai, score))
    
    return out
