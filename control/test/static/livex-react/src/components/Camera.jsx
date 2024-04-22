import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container, Stack } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import Dropdown from 'react-bootstrap/Dropdown';
import { TitleCard, WithEndpoint, ToggleSwitch, StatusBox, DropdownSelector } from 'odin-react';


const EndPointFormControl = WithEndpoint(Form.Control);
const EndpointDropdown = WithEndpoint(DropdownSelector);

function Camera(props) {
    const {cameraEndPoint} = props;
    const {connectedPuttingDisable} = props;

    return (

        <Container>
            <Col>
                <Stack>
                <InputGroup>
                    <InputGroup.Text>
                        command
                    </InputGroup.Text>
                    <EndPointFormControl
                        endpoint={cameraEndPoint}
                        type="text"
                        fullpath={"command"}
                        disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                </InputGroup>
                </Stack>
            </Col>
        </Container>

    )
}

export default Camera;

