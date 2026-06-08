import { Row, Col } from 'react-bootstrap';
import { useAdapterEndpoint } from 'odin-react';
import type { AdapterEndpoint } from 'odin-react';
import type { CameraEndpointTypes } from '../../EndpointTypes';

import OrcaCamera from './OrcaCamera';

interface CamerasProps {
  endpoint_url: string;
}


function Cameras(props: CamerasProps) {
    const {endpoint_url} = props;

    const cameraEndPoint = useAdapterEndpoint<CameraEndpointTypes>('camera', endpoint_url, 1000) as AdapterEndpoint<CameraEndpointTypes>;

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
              endpoint_url={endpoint_url}
              name={cameraEndPoint.data?.[key]?.camera_name}
            />
          </Col>
        ))
        }
      </Row>
    )
}

export default Cameras;

