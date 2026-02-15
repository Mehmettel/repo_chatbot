import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Video, Search, Folder, Sparkles } from 'lucide-react';
import { useEffect } from 'react';

export default function HomePage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary to-secondary">
      <div className="max-w-6xl mx-auto px-6 py-20">
        {/* Hero Section */}
        <div className="text-center text-white mb-20">
          <h1 className="text-6xl font-bold mb-6">MemeVault</h1>
          <p className="text-2xl font-light mb-8 opacity-90">
            AI destekli mizahi video arşivi
          </p>
          <p className="text-lg opacity-75 mb-12">
            Videolarınızı kaydedin, AI ile analiz edin, akıllıca arayın
          </p>
          
          <button
            onClick={() => navigate('/login')}
            className="bg-white text-primary px-8 py-4 rounded-xl font-semibold text-lg hover:bg-opacity-90 transition shadow-xl"
          >
            Hemen Başla
          </button>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 text-white">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 text-center">
            <Video size={48} className="mx-auto mb-4" />
            <h3 className="font-semibold text-lg mb-2">Video Yönetimi</h3>
            <p className="text-sm opacity-75">YouTube, Instagram, TikTok linklerini kaydedin</p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 text-center">
            <Sparkles size={48} className="mx-auto mb-4" />
            <h3 className="font-semibold text-lg mb-2">AI Analizi</h3>
            <p className="text-sm opacity-75">OpenAI ile otomatik video açıklaması</p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 text-center">
            <Search size={48} className="mx-auto mb-4" />
            <h3 className="font-semibold text-lg mb-2">Akıllı Arama</h3>
            <p className="text-sm opacity-75">Semantik arama ile tam istediğinizi bulun</p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 text-center">
            <Folder size={48} className="mx-auto mb-4" />
            <h3 className="font-semibold text-lg mb-2">Organize</h3>
            <p className="text-sm opacity-75">Klasörlerle videolarınızı düzenleyin</p>
          </div>
        </div>
      </div>
    </div>
  );
}
