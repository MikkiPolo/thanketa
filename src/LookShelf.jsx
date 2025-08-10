import React from 'react';

// LookShelf: простой блок «Полка + Заголовок»
// props: { look: { name, canvas: { ratio }, items: [{ id, src, x, y, w, z, r }] } }
const LookShelf = ({ look }) => {
  if (!look) return null;
  const ratio = Math.max(0.2, Math.min(2, look.canvas?.ratio || 0.8));

  return (
    <div className="look-shelf">
      <div className="look-title">{look.name || 'Образ'}</div>
      <div className="look-canvas" style={{ aspectRatio: `${1}/${ratio}` }}>
        {/* Белый холст */}
        <div className="look-stage">
          {(look.items || []).map(it => (
            <img
              key={it.id}
              className="look-item"
              loading="lazy"
              decoding="async"
              alt=""
              src={it.src}
              style={{
                left: `${it.x}%`,
                top: `${it.y}%`,
                width: `${it.w}%`,
                zIndex: it.z ?? 1,
                transform: `translate(-50%, -50%) rotate(${it.r || 0}deg)`,
                filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.12))'
              }}
              onError={(e) => {
                // graceful fallback: если webp не загрузился, пробуем png
                if (e.currentTarget.src.endsWith('.webp')) {
                  e.currentTarget.src = e.currentTarget.src.replace('.webp', '.png');
                }
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default LookShelf;


