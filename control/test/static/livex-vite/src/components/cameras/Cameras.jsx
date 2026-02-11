import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { useAdapterEndpoint } from 'odin-react';

import OrcaCamera from './OrcaCamera';

function Cameras(props) {
    const {endpoint_url} = props;
    const {connectedPuttingDisable} = props;

    const cameraEndPoint = useAdapterEndpoint('camera', endpoint_url, 1000);

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
              name={cameraEndPoint.data[key].camera_name}
              connectedPuttingDisable={connectedPuttingDisable}>
            </OrcaCamera>
          </Col>
        ))
        }
      </Row>
    )
}

export default Cameras;

