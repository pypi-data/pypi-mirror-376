// public/config.js
// Only set the API URL if it hasn't been set already (e.g., by runtime injection)
if (!window.__NEXT_PUBLIC_API_URL__) {
  // window.__NEXT_PUBLIC_API_URL__ = "http://4bd094a2-01.cloud.together.ai:4418"; // placeholder value
  // window.__NEXT_PUBLIC_API_URL__ = "https://virtueredbackend.virtueai.io"; // placeholder value
  window.__NEXT_PUBLIC_API_URL__ = "http://localhost:8008";
  // window.__NEXT_PUBLIC_API_URL__ = "http://localhost:8000";
}