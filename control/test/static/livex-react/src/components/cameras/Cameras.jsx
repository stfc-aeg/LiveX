import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import { useAdapterEndpoint } from 'odin-react';

import OrcaCamera from './OrcaCamera';


function Cameras(props) {
    const {connectedPuttingDisable} = props;

    const cameraEndPoint = useAdapterEndpoint('camera', 'http://192.168.0.22:8888', 5000);
    const liveViewEndPoint = useAdapterEndpoint('live_data', 'http://192.168.0.22:8888', 500);

    const [cameras, setCameras] = useState([]);

    useEffect(() => {
        const cameraArray = cameraEndPoint.data?.cameras;
        setCameras(cameraArray || []);
    }, [cameraEndPoint.data?.cameras]);  // Run only once after initial render

    return (
        <Container>
            <Col>
            {cameras.map((camera, index) => (
                <OrcaCamera
                    index={index}
                    connectedPuttingDisable={connectedPuttingDisable}
                    liveViewEndPoint={liveViewEndPoint}>
                </OrcaCamera>
            ))}
            </Col>
        </Container>
    )
}

export default Cameras;

