import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';

interface MapPopupCardProps {
  property: {
    id: number;
    title: string;
    price: number;
    property_type: string;
    media: { url: string }[];
    amenities?: string[];
  };
}

const MapPopupCard: React.FC<MapPopupCardProps> = ({ property }) => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const images = property.media && property.media.length > 0 
    ? property.media 
    : [{ url: 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&q=80&w=400' }];

  const nextImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev + 1) % images.length);
  };

  const prevImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  const handleShowMore = () => {
    window.open(`/listings/${property.id}`, '_blank');
  };

  return (
    <div className="w-64 overflow-hidden rounded-lg bg-white shadow-lg pointer-events-auto">
      {/* Image Carousel */}
      <div className="relative h-40 w-full group">
        <img
          src={images[currentImageIndex].url}
          alt={property.title}
          className="h-full w-full object-cover transition-transform duration-300 hover:scale-105"
        />
        
        {images.length > 1 && (
          <>
            <button
              onClick={prevImage}
              className="absolute left-1 top-1/2 -translate-y-1/2 p-1 rounded-full bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={nextImage}
              className="absolute right-1 top-1/2 -translate-y-1/2 p-1 rounded-full bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <ChevronRight size={16} />
            </button>
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
              {images.map((_, i) => (
                <div
                  key={i}
                  className={`h-1 w-1 rounded-full ${i === currentImageIndex ? 'bg-white' : 'bg-white/50'}`}
                />
              ))}
            </div>
          </>
        )}
      </div>

      {/* Details */}
      <div className="p-3">
        <h3 className="font-semibold text-gray-900 truncate">{property.title}</h3>
        <p className="text-sm text-blue-600 font-bold mt-1">
          ₹{property.price.toLocaleString()}<span className="text-gray-500 font-normal">/mo</span>
        </p>
        <div className="flex items-center gap-2 mt-2">
          <span className="text-xs px-2 py-1 bg-gray-100 rounded-full text-gray-600 uppercase tracking-wider font-medium">
            {property.property_type}
          </span>
        </div>

        {/* Action */}
        <button
          onClick={handleShowMore}
          className="w-full mt-3 flex items-center justify-center gap-2 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm"
        >
          Show More
          <ExternalLink size={14} />
        </button>
      </div>
    </div>
  );
};

export default MapPopupCard;
