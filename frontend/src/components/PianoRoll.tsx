/** SVG piano roll component — displays 3 octaves with highlighted active notes. */

import { useMemo } from 'react';
import { computePianoLayout, NOTE_COLORS } from '../utils/pianoGeometry';

interface PianoRollProps {
  activeNotes: number[];
  rootNote?: number;
  width?: number;
  height?: number;
  showLabels?: boolean;
  scale?: number;
}

function PianoRoll({
  activeNotes,
  rootNote,
  width,
  height,
  showLabels = false,
  scale = 1.0,
}: PianoRollProps) {
  const layout = useMemo(() => computePianoLayout(3, 3, scale), [scale]);
  const activeSet = useMemo(() => new Set(activeNotes), [activeNotes]);

  const svgWidth = width ?? layout.totalWidth;
  const svgHeight = height ?? layout.totalHeight;

  const whiteKeys = layout.keys.filter((k) => !k.isBlack);
  const blackKeys = layout.keys.filter((k) => k.isBlack);

  function keyFill(key: (typeof layout.keys)[0]): string {
    const active = activeSet.has(key.midiNote);
    const isRoot = rootNote !== undefined && key.midiNote % 12 === rootNote % 12;
    if (key.isBlack) {
      if (isRoot && active) return '#4ade80';
      if (active) return '#166534';
      return '#0a0a0a';
    }
    if (isRoot && active) return NOTE_COLORS.root;
    if (active) return NOTE_COLORS.whiteKeyActive;
    return NOTE_COLORS.whiteKeyDefault;
  }

  return (
    <svg
      width={svgWidth}
      height={svgHeight}
      viewBox={`0 0 ${layout.totalWidth} ${layout.totalHeight}`}
      xmlns="http://www.w3.org/2000/svg"
    >
      {whiteKeys.map((key) => (
        <g key={`w-${key.midiNote}`}>
          <rect
            x={key.x} y={key.y} width={key.width} height={key.height}
            fill={keyFill(key)} stroke="#555" strokeWidth={0.5} rx={1}
          />
          {showLabels && key.pitchClass === 0 && (
            <text
              x={key.x + key.width / 2} y={key.height - 4}
              textAnchor="middle" fontSize={10 * scale} fill="#888"
            >
              C{key.octave}
            </text>
          )}
        </g>
      ))}
      {blackKeys.map((key) => (
        <rect
          key={`b-${key.midiNote}`}
          x={key.x} y={key.y} width={key.width} height={key.height}
          fill={keyFill(key)} stroke="#333" strokeWidth={0.5} rx={1}
        />
      ))}
    </svg>
  );
}

export default PianoRoll;
