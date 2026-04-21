import NextAuth from "next-auth";
import KeycloakProvider from "next-auth/providers/keycloak";
import CredentialsProvider from "next-auth/providers/credentials";

const keycloakIssuer =
  process.env.KEYCLOAK_ISSUER ??
  `${process.env.KEYCLOAK_URL}/realms/${process.env.KEYCLOAK_REALM}`;

const isDev = process.env.NODE_ENV === "development";

const handler = NextAuth({
  providers: [
    KeycloakProvider({
      clientId: process.env.KEYCLOAK_CLIENT_ID ?? process.env.KEYCLOAK_ID ?? "",
      clientSecret: process.env.KEYCLOAK_CLIENT_SECRET ?? process.env.KEYCLOAK_SECRET ?? "",
      issuer: keycloakIssuer,
    }),
    // Lokale dev login — enkel actief in development mode
    ...(isDev
      ? [
          CredentialsProvider({
            id: "dev-login",
            name: "Dev Login (lokaal)",
            credentials: {
              username: { label: "Gebruiker", type: "text", placeholder: "koen" },
              password: { label: "Wachtwoord", type: "password" },
            },
            async authorize(credentials) {
              if (credentials?.username === "koen" && credentials?.password === "admin") {
                return {
                  id: "dev-koen",
                  name: "Koen Vorsters",
                  email: "koen@vorsternv.be",
                  image: null,
                  rol: "admin",
                };
              }
              return null;
            },
          }),
        ]
      : []),
  ],
  callbacks: {
    async jwt({ token, account, profile, user }) {
      if (account) {
        token.accessToken = account.access_token;
        token.idToken = account.id_token;
      }
      // Bewaar rol van credentials provider
      if (user && (user as Record<string, unknown>).rol) {
        token.rol = (user as Record<string, unknown>).rol as string;
      }
      if (profile) {
        token.picture = (profile as Record<string, unknown>).picture as string | undefined;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string | undefined;

      // Dev login: rol staat al op token
      if (token.rol) {
        session.user.rol = token.rol as string;
        return session;
      }

      // Rol uit Keycloak realm_access claims
      let roles: string[] = [];
      if (token.accessToken) {
        try {
          const parts = (token.accessToken as string).split(".");
          const payload = JSON.parse(
            Buffer.from(parts[1], "base64url").toString("utf-8")
          );
          roles = payload?.realm_access?.roles ?? [];
          // Naam/email fallback uit token
          if (!session.user.name && payload.name) session.user.name = payload.name;
          if (!session.user.email && payload.email) session.user.email = payload.email;
          if (!session.user.image && token.picture) session.user.image = token.picture as string;
        } catch {
          // JWT decode failed — keep defaults
        }
      }

      session.user.rol = roles.includes("admin")
        ? "admin"
        : roles.includes("tester")
          ? "tester"
          : "viewer";

      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  secret: process.env.NEXTAUTH_SECRET,
});

export { handler as GET, handler as POST };
