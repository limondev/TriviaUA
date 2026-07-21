// frontend/src/components/UkraineMap.tsx
import React, { useEffect, useState } from 'react';

interface Player {
  user_id: string;
  username: string;
  color: string;
}

interface UkraineMapProps {
  mapState: Record<string, { owner_id: string | null }>;
  players: Player[];
  onRegionClick?: (regionId: string) => void;
}

export const UkraineMap: React.FC<UkraineMapProps> = ({ mapState, players, onRegionClick }) => {
  const [svgContent, setSvgContent] = useState<string>('');

  // 1. Завантажуємо SVG із папки public/ukraine.svg
  useEffect(() => {
    fetch('/ukraine.svg')
      .then((res) => res.text())
      .then((data) => setSvgContent(data))
      .catch((err) => console.error('Помилка завантаження SVG:', err));
  }, []);

  // 2. Обробник кліків по областях
  const handleSvgClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (target.tagName.toLowerCase() === 'path') {
      const regionId = target.getAttribute('id');
      if (regionId && onRegionClick) {
        onRegionClick(regionId);
      }
    }
  };

  // 3. Генерація динамічних CSS-стилів для фарбування областей у колір гравця
  const generateDynamicStyles = () => {
    return players
      .map((player) => {
        const playerRegions = Object.entries(mapState)
          .filter(([_, data]) => data.owner_id === player.user_id)
          .map(([regionId]) => `#${regionId}`);

        if (playerRegions.length === 0) return '';

        return `
          ${playerRegions.join(', ')} {
            fill: ${player.color} !important;
            transition: fill 0.3s ease;
          }
        `;
      })
      .join('\n');
  };

  if (!svgContent) {
    return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>Завантаження мапи...</div>;
  }

  return (
    <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
      <style>{`
        /* Розміри SVG */
        #features {
          width: 100%;
          height: auto;
        }
        svg {
          width: 100% !important;
          height: auto !important;
          max-height: 380px;
        }
        /* Сірий дефолтний колір для нічиїх областей */
        #features path {
          fill: #334155;
          stroke: #0f172a;
          stroke-width: 1px;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        /* Ховер ефект при наведенні */
        #features path:hover {
          filter: brightness(1.3);
          stroke: #38bdf8 !important;
          stroke-width: 2px !important;
        }
        ${generateDynamicStyles()}
      `}</style>

      <div
        onClick={handleSvgClick}
        dangerouslySetInnerHTML={{ __html: svgContent }}
        style={{ width: '100%', display: 'flex', justifyContent: 'center' }}
      />
    </div>
  );
};