// Generate a UUID with graceful fallback for browsers without crypto.randomUUID
export function generateId(): string {
  const globalCrypto: Crypto | undefined = typeof crypto !== "undefined" ? crypto : undefined;

  if (globalCrypto && typeof globalCrypto.randomUUID === "function") {
    return globalCrypto.randomUUID();
  }

  const getRandom = () => {
    if (globalCrypto && typeof globalCrypto.getRandomValues === "function") {
      const arr = new Uint32Array(1);
      globalCrypto.getRandomValues(arr);
      return arr[0] / 0xffffffff;
    }
    return Math.random();
  };

  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = Math.floor(getRandom() * 16);
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
