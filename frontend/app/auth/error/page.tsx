import Link from "next/link";

const messages: Record<string, string> = {
  invalid_state: "Сессия входа устарела или не прошла проверку. Начните вход заново.",
  missing_configuration: "Подключение Radar к Arvexo Account ещё не настроено на сервере.",
  exchange_failed: "Arvexo Account не подтвердил одноразовый код входа.",
  invalid_profile: "Arvexo Account вернул неполный профиль пользователя.",
  account_unavailable: "Сервис Arvexo Account сейчас недоступен.",
};

export default async function AuthErrorPage({ searchParams }: { searchParams: Promise<{ reason?: string }> }) {
  const { reason } = await searchParams;
  return <main className="auth-status-page"><section><span className="auth-rings" aria-hidden="true"><i /><i /><i /></span><small>ARVEXO RADAR</small><h1>Не удалось войти</h1><p>{messages[reason ?? ""] ?? "Произошла ошибка авторизации."}</p><div><Link className="dark-button" href="/auth/login">Попробовать снова</Link><Link href="/">Вернуться на главную</Link></div></section></main>;
}
