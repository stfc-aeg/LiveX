import type { CameraEndpointTypes, LiveDataEndpointTypes } from '../../EndpointTypes';

import { Row, Col } from 'react-bootstrap';
import { useAdapterEndpoint } from 'odin-react';

import OrcaCamera from './OrcaCamera';

interface CamerasProps {
  endpoint_url: string;
}


function Cameras(props: CamerasProps) {
    const {endpoint_url} = props;

    const cameraEndPoint = useAdapterEndpoint<CameraEndpointTypes>('camera', endpoint_url, 1000);
    const liveViewEndPoint = useAdapterEndpoint<LiveDataEndpointTypes>('live_data', endpoint_url, 1000);

    // Destructuring data and cameras safely
    const cameras = cameraEndPoint?.data || {} // Fallback to an empty object if no data

    // console.log(cameras)

    return (
      <Row>
        {Object.keys(cameras).map((key) => (
          <Col 
            xs={12} sm={12} md={12} lg={6} xl={6} xxl={6}
            key={key}
          >
            <OrcaCamera
              endpoint={cameraEndPoint}
              liveViewEndPoint={liveViewEndPoint}
              name={cameraEndPoint.data?.[key]?.camera_name ?? 'Camera Not Found'}
            />
          </Col>
        ))
        }
      </Row>
    )
}

export default Cameras;

