import type { CameraEndpointTypes } from '../EndpointTypes';

import Row from 'react-bootstrap/Row';
import { useAdapterEndpoint } from 'odin-react';
import InferenceCard from './cameras/InferenceCard';

interface InferencePageProps {
  endpoint_url: string;
}

function InferencePage(props: InferencePageProps) {
    const { endpoint_url } = props;

    const cameraEndPoint = useAdapterEndpoint<CameraEndpointTypes>('camera', endpoint_url, 1000);

    // Destructuring data and cameras safely
    const cameras = cameraEndPoint?.data || {} // Fallback to an empty object if no data

    return (
      <Row>
        {Object.keys(cameras).map((key) => (
          <InferenceCard
            key={key}
            endpoint_url={endpoint_url}
            name={cameraEndPoint?.data?.[key]?.camera_name || 'Unknown Camera'}
          />
        ))}
      </Row>
    )
}

export default InferencePage;