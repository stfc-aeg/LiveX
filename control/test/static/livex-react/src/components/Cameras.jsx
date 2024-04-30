import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container, Stack } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { WithEndpoint, useAdapterEndpoint, OdinGraph } from 'odin-react';

import OrcaCamera from './OrcaCamera';



const EndPointFormControl = WithEndpoint(Form.Control);

function Cameras(props) {
    const {connectedPuttingDisable} = props;

    const cameraEndPoint = useAdapterEndpoint('camera', 'http://localhost:8888', 10000);
    const liveViewEndPoint = useAdapterEndpoint('live_data', 'http://localhost:8888', 10000);

    const [cameras, setCameras] = useState([]);

    useEffect(() => {
        console.log("sorting cam arrays");
        const cameraArray = cameraEndPoint.data?.cameras;
        setCameras(cameraArray || []);
    }, [cameraEndPoint.data?.cameras]);  // Run only once after initial render

    return (
        <Container>
            <Col>
            {cameras.map((camera, index) => (
                <OrcaCamera
                    index={index}
                    name={camera.camera_name}
                    cameraEndPoint={cameraEndPoint}
                    liveViewEndPoint={liveViewEndPoint}
                    connectedPuttingDisable={connectedPuttingDisable}>
                </OrcaCamera>
            ))}
            </Col>
        </Container>
    )
}

export default Cameras;

