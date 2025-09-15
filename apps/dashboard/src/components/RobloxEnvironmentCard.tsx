import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Box,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  CloudUpload as DeployIcon,
} from '@mui/icons-material';
import { RobloxEnvironment } from '../services/robloxSync';
import { GenerationStatus } from '../store/slices/robloxSlice';

interface RobloxEnvironmentCardProps {
  environment: RobloxEnvironment;
  generationStatus?: GenerationStatus;
  onGenerate: (id: string) => void;
  onDeploy: (id: string) => void;
  onDownload: (id: string) => void;
  onDelete: (id: string) => void;
  onPreview: (id: string) => void;
}

export const RobloxEnvironmentCard: React.FC<RobloxEnvironmentCardProps> = ({
  environment,
  generationStatus,
  onGenerate,
  onDeploy,
  onDownload,
  onDelete,
  onPreview,
}) => {
  const [menuAnchor, setMenuAnchor] = React.useState<null | HTMLElement>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'success';
      case 'generating': return 'warning';
      case 'deployed': return 'info';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'draft': return 'Draft';
      case 'generating': return 'Generating';
      case 'ready': return 'Ready';
      case 'deployed': return 'Deployed';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  const isGenerating = generationStatus?.status === 'generating';
  const canGenerate = environment.status === 'draft';
  const canDeploy = environment.status === 'ready' && environment.downloadUrl;
  const canDownload = environment.status === 'ready' && environment.downloadUrl;

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
          <Typography variant="h6" component="h3" noWrap>
            {environment.name}
          </Typography>
          <IconButton
            size="small"
            onClick={(e) => setMenuAnchor(e.currentTarget)}
          >
            <MoreIcon />
          </IconButton>
        </Box>

        <Typography color="text.secondary" gutterBottom>
          {environment.theme} • {environment.mapType.replace('_', ' ')}
        </Typography>

        <Box mb={2}>
          <Chip
            label={getStatusText(environment.status)}
            color={getStatusColor(environment.status)}
            size="small"
          />
        </Box>

        {environment.spec.learning_objectives && (
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary">
              Learning Objectives:
            </Typography>
            <Typography variant="body2">
              {environment.spec.learning_objectives.join(', ')}
            </Typography>
          </Box>
        )}

        {isGenerating && generationStatus && (
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {generationStatus.message}
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={generationStatus.progress || 0} 
            />
            <Typography variant="caption" color="text.secondary">
              {generationStatus.progress}% • {generationStatus.stage}
            </Typography>
          </Box>
        )}

        {environment.status === 'error' && generationStatus?.error && (
          <Typography variant="body2" color="error">
            Error: {generationStatus.error}
          </Typography>
        )}
      </CardContent>

      <CardActions>
        {canGenerate && (
          <Button
            startIcon={<PlayIcon />}
            onClick={() => onGenerate(environment.id)}
            variant="contained"
            color="primary"
          >
            Generate
          </Button>
        )}

        {canDownload && (
          <Button
            startIcon={<DownloadIcon />}
            onClick={() => onDownload(environment.id)}
            size="small"
          >
            Download
          </Button>
        )}

        {canDeploy && (
          <Button
            startIcon={<DeployIcon />}
            onClick={() => onDeploy(environment.id)}
            size="small"
            variant="outlined"
          >
            Deploy
          </Button>
        )}

        {environment.previewUrl && (
          <Button
            onClick={() => onPreview(environment.id)}
            size="small"
          >
            Preview
          </Button>
        )}
      </CardActions>

      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem onClick={() => {
          onDelete(environment.id);
          setMenuAnchor(null);
        }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default RobloxEnvironmentCard;
