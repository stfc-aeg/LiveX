import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container } from 'react-bootstrap';
import { useAdapterEndpoint } from 'odin-react';

import OrcaCamera from './OrcaCamera';

function Cameras(props) {
    const {endpoint_url} = props;
    const {connectedPuttingDisable} = props;

    const cameraEndPoint = useAdapterEndpoint('camera', endpoint_url, 5000);

    // Destructuring data and cameras safely
    const { data } = cameraEndPoint || {}; // Fallback to an empty object if cameraEndPoint is undefined
    const cameras = data?.cameras || {}; // Fallback to an empty object if data or cameras is undefined

    return (
      <Container>
        <Col>
          {Object.keys(cameras).map((key) => (
            <OrcaCamera
              key={key}
              endpoint_url={endpoint_url}
              name={cameraEndPoint.data.cameras[key].camera_name}
              connectedPuttingDisable={connectedPuttingDisable}>
            </OrcaCamera>
          ))
          }
        </Col>
      </Container>
    )
}

export default Cameras;

