import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { Container, Stack } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { useAdapterEndpoint, WithEndpoint, OdinGraph, StatusBox } from 'odin-react';
import Button from 'react-bootstrap/Button';

import LiveViewSocket from './LiveViewSocket';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function OrcaCamera(props) {
    const {index} = props;
    const {connectedPuttingDisable} = props;

    const indexString = index.toString();
    let orcaAddress = 'camera/cameras/'+indexString;
    const orcaEndPoint = useAdapterEndpoint(orcaAddress, 'http://localhost:8888', 0);
    const orcaData = orcaEndPoint?.data[index];

    return (

        <Container>
            <Col>
            <Row>
            <Col>
            <StatusBox as="span" label = "Status">
                {(orcaData?.status?.camera_status || "Not found" )}
            </StatusBox>
            </Col>
            {/* These buttons have variable output, display, and colour, depending on the camera status.
            Example, you can connect the camera if it is off, and disconnect if it's connected.
            Otherwise, you can't interact with it. You'd need to disarm it first.*/}
            <Col>
            <EndPointButton
                endpoint={orcaEndPoint}
                value={orcaData?.status?.camera_status === "connected" ? "disconnect" : "connect"}
                fullpath="command"
                event_type="click"
                disabled={!['connected', 'Disconnected'].includes(orcaData?.status?.camera_status)}
                variant={orcaData?.status?.camera_status==="connected" ? "warning" : "success"}>
                {orcaData?.status?.camera_status==="connected" ? 'Disconnect' : 'Connect'}
            </EndPointButton>
            </Col>
            <Col>
            <EndPointButton
                endpoint={orcaEndPoint}
                value={orcaData?.status?.camera_status === "armed" ? "disarm" : "arm"}
                fullpath="command"
                event_type="click"
                disabled={!['armed', 'connected'].includes(orcaData?.status?.camera_status)}
                variant={orcaData?.status?.camera_status==="armed" ? "warning" : "success"}>
                {orcaData?.status?.camera_status==="armed" ? 'Disarm' : 'Arm'}
            </EndPointButton>
            </Col>
            <Col>
            <EndPointButton
                endpoint={orcaEndPoint}
                value={orcaData?.status?.camera_status === "capturing" ? "discapture" : "capture"}
                fullpath="command"
                event_type="click"
                disabled={!['capturing', 'armed'].includes(orcaData?.status?.camera_status)}
                variant={orcaData?.status?.camera_status==="capturing" ? "warning" : "success"}>
                {orcaData?.status?.camera_status==="capturing" ? 'Stop Capturing' : 'Capture'}
            </EndPointButton>
            </Col>
            </Row>
                <Stack>
                <InputGroup>
                    <InputGroup.Text>
                        command
                    </InputGroup.Text>
                    <EndPointFormControl
                        endpoint={orcaEndPoint}
                        type="text"
                        fullpath="command"
                        disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                </InputGroup>
                </Stack>

                <Stack>
                <InputGroup>
                    <InputGroup.Text>
                        exposure_time
                    </InputGroup.Text>
                    <EndPointFormControl
                        endpoint={orcaEndPoint}
                        type="number"
                        fullpath="config/exposure_time"
                        disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                </InputGroup>
                </Stack>

                <LiveViewSocket
                name={orcaData?.camera_name}>
                </LiveViewSocket>

            </Col>
        </Container>

    )
}

export default OrcaCamera;

