/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Isso diz ao Next.js para ignorar erros de falta de parâmetros na exportação das páginas dinâmicas
  distDir: 'out',
};

export default nextConfig;