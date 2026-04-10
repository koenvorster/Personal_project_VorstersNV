import NextAuth from "next-auth";
import KeycloakProvider from "next-auth/providers/keycloak";

const handler = NextAuth({
  providers: [
    KeycloakProvider({
      clientId: process.env.KEYCLOAK_ID!,
      clientSecret: process.env.KEYCLOAK_SECRET ?? "",
      issuer: process.env.KEYCLOAK_ISSUER,
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.idToken = account.id_token;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      // Rol uit Keycloak realm_access
      const payload = token.accessToken
        ? JSON.parse(Buffer.from((token.accessToken as string).split(".")[1], "base64").toString())
        : {};
      const roles: string[] = payload?.realm_access?.roles ?? [];
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
});

export { handler as GET, handler as POST };
