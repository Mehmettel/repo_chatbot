import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../../services/api';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoMessage, setDemoMessage] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleEnsureDemo = async () => {
    setDemoMessage('');
    setDemoLoading(true);
    try {
      const res = await authAPI.ensureDemo();
      setDemoMessage(res.data?.message || 'Örnek hesap hazır. Yukarıdaki bilgilerle giriş yapın.');
      setEmail('deneme@gmail.com');
      setPassword('deneme');
    } catch (err) {
      setDemoMessage(err.response?.data?.detail || 'Backend erişilemiyor. Docker ve API çalışıyor mu?');
    } finally {
      setDemoLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Giriş başarısız');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          E-posta
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="ornek@email.com"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Şifre
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="••••••••"
          required
        />
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      <p className="text-xs text-gray-500 text-center">
        Örnek hesap: <strong>deneme@gmail.com</strong> / <strong>deneme</strong>
      </p>
      <button
        type="button"
        onClick={handleEnsureDemo}
        disabled={demoLoading}
        className="w-full py-2 text-sm text-primary border border-primary rounded-lg hover:bg-primary/5 disabled:opacity-50 transition"
      >
        {demoLoading ? 'Hazırlanıyor...' : 'Örnek hesabı hazırla'}
      </button>
      {demoMessage && (
        <div className={`p-3 rounded-lg text-sm ${demoMessage.includes('hazır') ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}>
          {demoMessage}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 bg-primary text-white rounded-lg font-medium hover:bg-opacity-90 disabled:bg-gray-400 transition"
      >
        {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
      </button>
    </form>
  );
}
