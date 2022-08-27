/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
}

module.exports = nextConfig

// module.exports = () => {
//   const rewrites = () => {
//     return [
//       {
//         source: "/reharm/:path*",
//         destination: "http://localhost:5000/reharm/:path*",
//       },
//     ];
//   };
//   return {
//     rewrites,
//   };
// };