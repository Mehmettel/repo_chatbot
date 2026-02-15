import { useState } from 'react';
import { Link } from 'react-router-dom';
import LoginForm from '../components/Auth/LoginForm';
import RegisterForm from '../components/Auth/RegisterForm';

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary to-secondary flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary mb-2">MemeVault</h1>
          <p className="text-gray-600 text-sm">AI destekli video arşivi</p>
        </div>

        <div className="flex border-b mb-6">
          <button
            onClick={() => setIsRegister(false)}
            className={`flex-1 pb-3 text-sm font-medium transition ${
              !isRegister
                ? 'border-b-2 border-primary text-primary'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Giriş Yap
          </button>
          <button
            onClick={() => setIsRegister(true)}
            className={`flex-1 pb-3 text-sm font-medium transition ${
              isRegister
                ? 'border-b-2 border-primary text-primary'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Kayıt Ol
          </button>
        </div>

        {isRegister ? <RegisterForm /> : <LoginForm />}
      </div>
    </div>
  );
}
