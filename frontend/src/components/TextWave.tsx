import { useEffect } from 'react';
import { useTextWave } from '../hooks/useTextWave';
import '../styles/text-wave.css';

type TextWaveProps = {
  text: string;
  as?: keyof JSX.IntrinsicElements;
  className?: string;
  active?: boolean;
};

export function TextWave({ text, as: Component = 'h1', className = '', active = true }: TextWaveProps) {
  const ref = useTextWave(active);

  useEffect(() => {
    if (ref.current) {
      ref.current.setAttribute('role', 'presentation');
    }
  }, [ref]);

  return (
    <Component className={`text-wave ${className}`}>
      <span ref={ref} data-textwave-content={text}>
        {text}
      </span>
    </Component>
  );
}

