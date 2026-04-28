import s from './MusicalitySlider.module.css';

interface Props {
  value: number;
  onChange: (value: number) => void;
}

function MusicalitySlider({ value, onChange }: Props) {
  return (
    <div className={s.wrapper}>
      <label className={s.label}>
        <span>Musicality</span>
        <span className={s.value}>{value.toFixed(2)}</span>
      </label>
      <div className={s.sliderRow}>
        <span className={s.endLabel}>Standard</span>
        <input
          className={s.slider}
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
        />
        <span className={s.endLabel}>Complex</span>
      </div>
    </div>
  );
}

export default MusicalitySlider;
