import { useEffect, useRef } from 'react';

const LETTER_DELAY = 35;
const WAVE_RANGE = 8;

export function useTextWave(enabled: boolean) {
  const ref = useRef<HTMLSpanElement>(null);
  const animationFrameRef = useRef<number>();

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const originalText = element.dataset.textwaveContent ?? element.textContent ?? '';
    if (!originalText) return;

    element.innerHTML = '';

    const letters: HTMLSpanElement[] = [];

    const words = originalText.split(' ');
    words.forEach((word, wordIndex) => {
      const wordWrapper = document.createElement('span');
      wordWrapper.className = 'wave-word';

      Array.from(word).forEach((char) => {
        const charSpan = document.createElement('span');
        charSpan.className = 'wave-char';
        charSpan.textContent = char;
        wordWrapper.appendChild(charSpan);
        letters.push(charSpan);
      });

      element.appendChild(wordWrapper);

      if (wordIndex < words.length - 1) {
        const space = document.createElement('span');
        space.className = 'wave-space';
        space.textContent = ' ';
        element.appendChild(space);
      }
    });

    let progress = -WAVE_RANGE;

    const animateWave = () => {
      progress += 0.6;

      letters.forEach((span, index) => {
        const offset = Math.abs(progress - index);
        if (offset > WAVE_RANGE) {
          span.style.transform = 'translateY(0)';
          span.style.opacity = '1';
          return;
        }

        const normalized = 1 - offset / WAVE_RANGE;
        const translate = Math.sin(normalized * Math.PI) * -14;
        span.style.transform = `translateY(${translate.toFixed(2)}px)`;
        span.style.opacity = (0.85 + normalized * 0.15).toString();
      });

      if (progress < letters.length + WAVE_RANGE) {
        animationFrameRef.current = requestAnimationFrame(animateWave);
      }
    };

    const handleEnter = () => {
      if (!enabled) return;
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      progress = -WAVE_RANGE;
      animationFrameRef.current = requestAnimationFrame(animateWave);
    };

    element.addEventListener('mouseenter', handleEnter);

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      element.removeEventListener('mouseenter', handleEnter);
      element.innerHTML = originalText;
    };
  }, [enabled]);

  return ref;
}
