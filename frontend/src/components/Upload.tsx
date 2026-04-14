import React, { useRef, useState } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  useTheme, 
  alpha, 
  LinearProgress, 
  Alert,
  IconButton
} from '@mui/material';
import { 
  CloudUpload, 
  AddToDrive, 
  CloudQueue,
  DeleteOutline
} from '@mui/icons-material';

interface UploadProps {
  onFilesSelected: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string;
}

const Upload: React.FC<UploadProps> = ({ 
  onFilesSelected, 
  maxFiles = 10,
  acceptedTypes = "image/png,image/jpeg,application/pdf"
}) => {
  const theme = useTheme();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [simulatingCloud, setSimulatingCloud] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      if (selectedFiles.length + newFiles.length > maxFiles) {
        setError(`Maximum of ${maxFiles} files allowed.`);
        return;
      }
      const updatedFiles = [...selectedFiles, ...newFiles];
      setSelectedFiles(updatedFiles);
      onFilesSelected(updatedFiles);
      setError(null);
    }
  };

  const removeFile = (index: number) => {
    const updated = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(updated);
    onFilesSelected(updated);
  };

  const simulateCloudPicker = (provider: string) => {
    setSimulatingCloud(true);
    setError(null);
    
    // Open a popup picker window
    const pickerWindow = window.open('', '_blank', 'width=500,height=600');
    if (pickerWindow) {
      pickerWindow.document.write(`
        <body style="font-family: sans-serif; text-align: center; padding: 40px; background: #f9f9f9;">
          <div style="border: 1px solid #ddd; padding: 20px; border-radius: 12px; background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h2 style="color: #1a73e8;">Connecting to ${provider === 'google_drive' ? 'Google Drive' : 'OneDrive'}</h2>
            <p>Please authorize Rentora to access your cloud storage.</p>
            <div style="margin: 20px 0;">
              <div style="width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; margin-left: auto; margin-right: auto;"></div>
            </div>
            <p style="color: gray; font-size: 0.8rem;">(Simulated Secure OAuth2 Flow)</p>
          </div>
          <style>
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
          </style>
        </body>
      `);
      
      setTimeout(() => {
        if (!pickerWindow.closed) pickerWindow.close();
        
        const blob = new Blob(["mock content"], { type: "image/jpeg" });
        const mockFile = new File([blob], `imported_from_${provider}_${Math.floor(Math.random()*1000)}.jpg`, { type: "image/jpeg" });
        
        setSelectedFiles(prev => {
          const updated = [...prev, mockFile];
          onFilesSelected(updated);
          return updated;
        });
        setSimulatingCloud(false);
      }, 3000);
    } else {
      setError("Popup blocked! Please allow popups for cloud selection.");
      setSimulatingCloud(false);
    }
  };

  return (
    <Box>
      <Box 
        sx={{ 
          p: 5, 
          border: `2px dashed ${theme.palette.divider}`, 
          borderRadius: 4,
          bgcolor: alpha(theme.palette.primary.main, 0.02),
          mb: 3,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          transition: 'all 0.2s',
          '&:hover': {
            bgcolor: alpha(theme.palette.primary.main, 0.05),
          }
        }}
        onClick={() => fileInputRef.current?.click()}
        style={{ cursor: 'pointer' }}
      >
        <input 
          type="file" 
          multiple 
          hidden 
          ref={fileInputRef} 
          onChange={handleFileChange}
          accept={acceptedTypes}
        />
        <CloudUpload sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" fontWeight={700}>Click to Upload Local Files</Typography>
        <Typography variant="body2" color="text.secondary">PNG, JPG, or PDF allowed.</Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Box display="flex" gap={2} justifyContent="center" mb={4}>
        <Button 
          variant="outlined" 
          startIcon={<AddToDrive />}
          onClick={() => simulateCloudPicker('google_drive')}
          disabled={simulatingCloud}
        >
          {simulatingCloud ? 'Connecting...' : 'Google Drive'}
        </Button>
        <Button 
          variant="outlined" 
          startIcon={<CloudQueue />}
          onClick={() => simulateCloudPicker('onedrive')}
          disabled={simulatingCloud}
        >
          {simulatingCloud ? 'Connecting...' : 'OneDrive'}
        </Button>
      </Box>

      {simulatingCloud && <LinearProgress sx={{ mb: 3 }} />}

      {selectedFiles.length > 0 && (
        <Box>
          <Typography variant="subtitle2" mb={1} fontWeight={600}>Selected Files ({selectedFiles.length})</Typography>
          <Box display="flex" flexDirection="column" gap={1}>
            {selectedFiles.map((f, i) => (
              <Box 
                key={i} 
                display="flex" 
                alignItems="center" 
                justifyContent="space-between"
                sx={{ p: 1, bgcolor: 'background.paper', border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}
              >
                <Typography variant="caption" noWrap sx={{ maxWidth: '80%' }}>{f.name}</Typography>
                <IconButton size="small" color="error" onClick={() => removeFile(i)}>
                  <DeleteOutline fontSize="small" />
                </IconButton>
              </Box>
            ))}
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default Upload;
