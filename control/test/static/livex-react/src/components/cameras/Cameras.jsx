import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
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
      <Row>
        {Object.keys(cameras).map((key) => (
          <Col xs={12} sm={12} md={12} lg={6} xl={6} xxl={6}>
            <OrcaCamera
              key={key}
              endpoint_url={endpoint_url}
              name={cameraEndPoint.data.cameras[key].camera_name}
              connectedPuttingDisable={connectedPuttingDisable}>
            </OrcaCamera>
          </Col>
        ))
        }
      </Row>
    )
}

export default Cameras;

