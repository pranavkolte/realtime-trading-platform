import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface PriceChartProps {
  data: number[];
  width?: number;
  height?: number;
  currentPrice?: number; // Add this line
}

export const PriceChart: React.FC<PriceChartProps> = ({ 
  data, 
  width = '100%', 
  height = 200 
}) => {
  // Transform the data for Recharts
  const chartData = data.map((price, index) => ({
    time: index + 1,
    price: price
  }));

  // Calculate price range for Y-axis
  const minPrice = Math.min(...data) * 0.98;
  const maxPrice = Math.max(...data) * 1.02;

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="time" 
            stroke="#6b7280"
            fontSize={12}
            tickFormatter={(value) => `${value}`}
          />
          <YAxis 
            stroke="#6b7280"
            fontSize={12}
            domain={[minPrice, maxPrice]}
            tickFormatter={(value) => `$${value.toFixed(2)}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '6px'
            }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#2563eb" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#2563eb' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};