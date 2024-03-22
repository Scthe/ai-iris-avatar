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

export function useIsWindowScrolledToBottomRef() {
  const resultRef = useRef(isWindowScrolledToBottom());

  useEffect(() => {
    function scrollHandler() {
      resultRef.current = isWindowScrolledToBottom();
    }
    window.addEventListener('scroll', scrollHandler);
    return () => {
      window.removeEventListener('scroll', scrollHandler);
    };
  }, []);

  return resultRef;
}

function isWindowScrolledToBottom(margin = 50) {
  const scrollPos = window.innerHeight + window.scrollY;
  const distanceToBottom = document.body.offsetHeight - scrollPos;
  /*console.log(distanceToBottom, {
    innerHeight: window.innerHeight,
    scrollY: window.scrollY,
    document_body_offsetHeight: document.body.offsetHeight,
  });*/
  return distanceToBottom < margin;
}
