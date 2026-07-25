import React, { useEffect, useState } from 'react';

interface Player {
  user_id: string;
  username: string;
  color: string;
}

interface RegionData {
  owner_id: string | null;
  is_capital?: boolean;
}

interface UkraineMapProps {
  mapState: Record<string, RegionData>;
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

  // 3. Динамічні CSS-стилі для кольору гравців ТА виділення Замків 🏰
  const generateDynamicStyles = () => {
    let styles = '';

    // А) Фарбуємо області гравців
    players.forEach((player) => {
      const playerRegions = Object.entries(mapState)
        .filter(([_, data]) => data.owner_id === player.user_id)
        .map(([regionId]) => `#${regionId}`);

      if (playerRegions.length > 0) {
        styles += `
          ${playerRegions.join(', ')} {
            fill: ${player.color} !important;
            transition: fill 0.3s ease;
          }
        `;
      }
    });

    // Б) Додаємо золоту неонову рамку для Столиць (Замків) 🏰
    const capitalRegions = Object.entries(mapState)
      .filter(([_, data]) => data.is_capital === true)
      .map(([regionId]) => `#${regionId}`);

    if (capitalRegions.length > 0) {
      styles += `
        ${capitalRegions.join(', ')} {
          stroke: #facc15 !important;
          stroke-width: 3px !important;
          stroke-dasharray: 4;
          filter: drop-shadow(0 0 6px #facc15);
        }
      `;
    }

    return styles;
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
          max-height: 480px;
        }
        /* Сірий дефолтний колір для нічиїх областей */
        #features path, svg path {
          fill: #334155;
          stroke: #0f172a;
          stroke-width: 1px;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        /* Ховер ефект при наведенні */
        #features path:hover, svg path:hover {
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