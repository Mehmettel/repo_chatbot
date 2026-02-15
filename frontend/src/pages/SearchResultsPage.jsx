import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { searchAPI, videosAPI } from '../services/api';
import Header from '../components/Layout/Header';
import VideoGrid from '../components/Video/VideoGrid';
import { ArrowLeft, Sparkles } from 'lucide-react';

export default function SearchResultsPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q') || '';

  const { data, isLoading, error } = useQuery({
    queryKey: ['search', query],
    queryFn: () => searchAPI.search(query).then(res => res.data),
    enabled: !!query,
  });

  // Arama sonuçlarından video ID'leri al ve tam video detaylarını çek
  const videoIds = data?.results?.map(r => r.video_id) || [];
  
  const { data: allVideos } = useQuery({
    queryKey: ['videos'],
    queryFn: () => videosAPI.list().then(res => res.data),
    enabled: videoIds.length > 0,
  });

  // Arama sonuçlarını tam video objelerine dönüştür
  const videos = data?.results?.map(result => {
    const fullVideo = allVideos?.find(v => v.id === result.video_id);
    return {
      ...fullVideo,
      id: result.video_id,
      score: result.score,
      search_score: result.score,
    };
  }).filter(v => v && v.status === 'COMPLETED') || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 transition-colors">
      <Header />
      
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-primary dark:hover:text-primary transition-colors mb-6 group"
          >
            <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
            <span>Dashboard'a Dön</span>
          </button>

          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center">
              <Sparkles className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">
                Arama Sonuçları
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                <span className="font-medium text-primary">"{query}"</span> için bulunanlar
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4 mt-4">
            <div className="px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
              <span className="text-2xl font-bold text-primary">{videos.length}</span>
              <span className="text-sm text-gray-600 dark:text-gray-300 ml-2">video bulundu</span>
            </div>
            {videos.length > 0 && (
              <div className="px-4 py-2 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/30 dark:to-blue-900/30 text-green-700 dark:text-green-400 rounded-lg text-sm font-medium flex items-center gap-2 border border-green-200 dark:border-green-800">
                <span className="text-base">🔍</span>
                <span>Hybrid Search (Semantik + Anahtar Kelime)</span>
              </div>
            )}
          </div>
        </div>

        {isLoading && (
          <div className="flex flex-col items-center justify-center py-32">
            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
            <div className="text-gray-600 font-medium">AI ile aranıyor...</div>
            <div className="text-sm text-gray-400 mt-2">Video açıklamaları analiz ediliyor</div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
            <div className="font-semibold mb-1">Arama sırasında bir hata oluştu</div>
            <div className="text-sm text-red-600">Lütfen tekrar deneyin veya farklı kelimeler kullanın</div>
          </div>
        )}

        {!isLoading && !error && videos.length === 0 && (
          <div className="flex flex-col items-center justify-center py-32 px-4">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-6">
              <Sparkles size={48} className="text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Sonuç bulunamadı
            </h3>
            <p className="text-sm text-gray-500 text-center max-w-md">
              "<span className="font-medium text-gray-700">{query}</span>" ile eşleşen tamamlanmış video yok
            </p>
            <p className="text-xs text-gray-400 mt-4">
              💡 İpucu: Farklı kelimeler deneyin veya videoların işlenmesini bekleyin
            </p>
          </div>
        )}

        {!isLoading && !error && videos.length > 0 && (
          <div className="space-y-4">
            <div className="text-sm text-gray-700 dark:text-gray-300 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/30 dark:to-indigo-900/30 border border-blue-200 dark:border-blue-700 rounded-xl p-5 flex items-start gap-3 shadow-sm">
              <span className="text-2xl">🤖</span>
              <div className="flex-1">
                <strong className="block mb-2 text-base text-gray-800 dark:text-gray-100">Gelişmiş AI Arama Sistemi</strong>
                <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                  <p>
                    <strong className="text-primary">🔍 Hybrid Search:</strong> Sorgunuz hem <em>semantik anlamına</em> göre (GPT-4o + text-embedding-3-small) 
                    hem de <em>anahtar kelimelere</em> göre (PostgreSQL Full-Text Search) aranır.
                  </p>
                  <p>
                    <strong className="text-purple-600 dark:text-purple-400">🎬 Multi-Frame Analiz:</strong> Her videonun 3 farklı anından kare çekilerek 
                    baştan sona kapsamlı görsel analiz yapılır.
                  </p>
                  <p>
                    <strong className="text-blue-600 dark:text-blue-400">🎙️ Whisper Transkript:</strong> Video sesleri metne çevrilerek konuşmalar da arama kapsamına dahil edilir.
                  </p>
                  {videos.length === 1 && (
                    <p className="mt-3 pt-2 border-t border-blue-200 dark:border-blue-700 italic text-gray-500">
                      ℹ️ Şu an sistemde {videos.length} video var. Daha fazla video eklendikçe arama sonuçları çeşitlenecektir.
                    </p>
                  )}
                </div>
              </div>
            </div>
            <VideoGrid videos={videos} />
          </div>
        )}
      </div>
    </div>
  );
}
