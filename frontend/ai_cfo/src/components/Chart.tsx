interface ChartProps {
  title: string;
  data: number[];
  color: string;
}

export default function Chart({ title, data, color }: ChartProps) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min;

  return (
    <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
      <h3 className="text-lg font-semibold text-[#2E2E2E] mb-4 font-['Space_Grotesk']">{title}</h3>

      <div className="relative h-48">
        <svg className="w-full h-full" viewBox="0 0 400 160" preserveAspectRatio="none">
          <defs>
            <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={color} stopOpacity="0.3" />
              <stop offset="100%" stopColor={color} stopOpacity="0.05" />
            </linearGradient>
          </defs>

          <g>
            {data.map((value, i) => {
              const x = (i / (data.length - 1)) * 400;
              const y = 160 - ((value - min) / range) * 140 - 10;
              const nextX = ((i + 1) / (data.length - 1)) * 400;
              const nextY =
                i < data.length - 1 ? 160 - ((data[i + 1] - min) / range) * 140 - 10 : y;

              return (
                <g key={i}>
                  {i < data.length - 1 && (
                    <line
                      x1={x}
                      y1={y}
                      x2={nextX}
                      y2={nextY}
                      stroke={color}
                      strokeWidth="3"
                      className="transition-all duration-500"
                      style={{
                        strokeDasharray: '400',
                        strokeDashoffset: '400',
                        animation: 'draw 2s ease-out forwards',
                        animationDelay: `${i * 0.05}s`,
                      }}
                    />
                  )}
                  <circle
                    cx={x}
                    cy={y}
                    r="4"
                    fill={color}
                    className="transition-all duration-300 hover:r-6"
                    style={{
                      opacity: 0,
                      animation: 'fadeIn 0.3s ease-out forwards',
                      animationDelay: `${i * 0.05 + 0.5}s`,
                    }}
                  />
                </g>
              );
            })}
          </g>

          <path
            d={`M 0 160 ${data
              .map((value, i) => {
                const x = (i / (data.length - 1)) * 400;
                const y = 160 - ((value - min) / range) * 140 - 10;
                return `L ${x} ${y}`;
              })
              .join(' ')} L 400 160 Z`}
            fill={`url(#gradient-${color})`}
            className="transition-all duration-500"
            style={{
              opacity: 0,
              animation: 'fadeIn 1s ease-out forwards',
              animationDelay: '0.5s',
            }}
          />
        </svg>
      </div>

      <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
        <span>12 months ago</span>
        <span>Today</span>
      </div>
    </div>
  );
}
