import type { CameraEndpointTypes, CameraType, LiveDataEndpointTypes } from '../../EndpointTypes';

import { Row, Col } from 'react-bootstrap';
import { useAdapterEndpoint } from '@dssg/odin-react';

import OrcaCamera from './OrcaCamera';

interface CamerasProps {
  endpoint_url: string;
}


function Cameras(props: CamerasProps) {
    const {endpoint_url} = props;

    const cameraEndPoint = useAdapterEndpoint<CameraEndpointTypes>('camera', endpoint_url, 1000);
    const liveViewEndPoint = useAdapterEndpoint<LiveDataEndpointTypes>('liveview', endpoint_url, 1000);

    const camera_names = cameraEndPoint?.data?.camera_names ?? [];
    const cameras = cameraEndPoint?.data?.cameras;

    return (
      <Row>
        {camera_names.map((camera_name) => {
          const camera = cameras?.[camera_name] as CameraType | undefined;
          return (
            <Col
              xs={12} sm={12} md={12} lg={6} xl={6} xxl={6}
              key={camera_name}
            >
              <OrcaCamera
                endpoint={cameraEndPoint}
                liveViewEndPoint={liveViewEndPoint}
                name={camera?.camera_name ?? camera_name}
              />
            </Col>
          );
        })}
      </Row>
    )
}

export default Cameras;

