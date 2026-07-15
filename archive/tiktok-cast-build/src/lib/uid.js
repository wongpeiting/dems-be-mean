let instanceCount = 0;

export function nextUid() {
  return `uid-${++instanceCount}`;
}
