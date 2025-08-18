import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface PriceChartProps {
  data: number[];
  timestamps?: string[]; // <-- Add timestamps prop
  width?: number;
  height?: number;
  currentPrice?: number;
}

export const PriceChartChartJS: React.FC<PriceChartProps> = ({ 
  data, 
  timestamps, // <-- Accept timestamps
  height = 200 
}) => {
  // Format timestamps for x-axis labels
  const labels: string[] = timestamps
    ? timestamps.map(ts => {
        const d = new Date(ts);
        // Show only HH:MM:SS
        return d.toLocaleTimeString('en-IN', { hour12: false });
      })
    : data.map((_, index) => (index + 1).toString());

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Price',
        data: data,
        borderColor: '#2563eb',
        backgroundColor: 'rgba(37, 99, 235, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => `Price: $${context.parsed.y.toFixed(2)}`,
        },
      },
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false,
        },
        ticks: {
          maxTicksLimit: 8, // Show fewer ticks for readability
        },
      },
      y: {
        display: true,
        ticks: {
          callback: (value: any) => `$${value.toFixed(2)}`,
        },
      },
    },
  };

  return (
    <div style={{ height: `${height}px` }}>
      <Line data={chartData} options={options} />
    </div>
  );
};