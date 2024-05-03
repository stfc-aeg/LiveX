import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container, Stack } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import { WithEndpoint, useAdapterEndpoint, OdinGraph } from 'odin-react';

import OrcaCamera from './OrcaCamera';


function Cameras(props) {
    const {connectedPuttingDisable} = props;

    const cameraEndPoint = useAdapterEndpoint('camera', 'http://localhost:8888', 5000);

    const [cameras, setCameras] = useState([]);

    useEffect(() => {
        console.log("sorting cam arrays");
        const cameraArray = cameraEndPoint.data?.cameras;
        setCameras(cameraArray || []);
        console.log("cameraArray:", cameraArray);
    }, [cameraEndPoint.data?.cameras]);  // Run only once after initial render

    return (
        <Container>
            <Col>
            {cameras.map((camera, index) => (
                <OrcaCamera
                    index={index}
                    connectedPuttingDisable={connectedPuttingDisable}>
                </OrcaCamera>
            ))}
            </Col>
        </Container>
    )
}

export default Cameras;

