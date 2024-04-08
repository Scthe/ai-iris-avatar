import { useRef, useEffect } from 'https://esm.sh/preact/hooks';

export const toggleElementInArr = (arr, item) =>
  arr.includes(item) ? arr.filter((i) => i !== item) : [...arr, item];

export function cx(...args) {
  return args
    .flatMap((part) => {
      switch (typeof part) {
        case 'string':
          return [part];
        case 'undefined':
        case 'boolean':
          return [''];
        case 'object':
          return Object.entries(part).map(([k, v]) => (Boolean(v) ? k : ''));
        default:
          throw new Error('Invalid agument for cx:', JSON.stringify(part));
      }
    })
    .join(' ');
}

export function useLatest(value) {
  const ref = useRef(value);
  ref.current = value;
  return ref;
}

export function randId() {
  return Math.random()
    .toString(36)
    .replace(/[^a-z]+/g, '')
    .substr(2, 10);
}
