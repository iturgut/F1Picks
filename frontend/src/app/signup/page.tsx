import { SignupForm } from '@/components/auth/SignupForm'

export const metadata = {
  title: 'Sign Up - F1 Picks',
  description: 'Create your F1 Picks account',
}

export default function SignupPage() {
  return (
    <div className="flex min-h-screen flex-col justify-center px-6 py-12 lg:px-8 bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="text-5xl font-bold text-red-600">🏎️</div>
        </div>
        <h1 className="mt-6 text-center text-4xl font-bold tracking-tight text-gray-900">
          F1 Picks
        </h1>
      </div>

      <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white px-6 py-12 shadow-xl rounded-lg sm:px-12">
          <SignupForm />
        </div>
      </div>
    </div>
  )
}
