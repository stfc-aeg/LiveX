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

function Metadata(props) {
    const {liveXEndPoint} = props;
    const {connectedPuttingDisable} = props;

    return (
        <TitleCard title="metadata" type="warning">
        <Container>
        <Row>
            <Col xs={8}>
            dummy words
            </Col>
            <Col>
            <StatusBox
                type="info"
                label="date">
                    {liveXEndPoint.data.metadata?.date}
            </StatusBox>
            </Col>

        </Row>
        <Row>
            <Col xs={4}>
            <InputGroup>
                <InputGroup.Text>
                    spinner
                </InputGroup.Text>
                <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"metadata/spinner"}
                    disabled={connectedPuttingDisable}>
                </EndPointFormControl>
            </InputGroup>
            <InputGroup>
                <InputGroup.Text>
                    freetext
                </InputGroup.Text>
                <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="text"
                    fullpath={"metadata/freetext"}
                    disabled={connectedPuttingDisable}>
                </EndPointFormControl>
            </InputGroup>
            </Col>

            <Col>
                <Stack>
                <InputGroup>
                    <InputGroup.Text>
                        comment
                    </InputGroup.Text>
                    <EndPointFormControl
                        endpoint={liveXEndPoint}
                        type="text"
                        fullpath={"metadata/comment"}
                        disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                </InputGroup>
                </Stack>

              <EndpointDropdown
                endpoint={liveXEndPoint} event_type="select"
                fullpath="metadata/sample"
                buttonText={
                    liveXEndPoint.data.metadata?.dropdowns.samples[liveXEndPoint.data.metadata.dropdowns.samples_index] || "Unknown"} disabled={connectedPuttingDisable}>
                {liveXEndPoint.data.metadata?.dropdowns.samples ? liveXEndPoint.data.metadata?.dropdowns.samples.map(
                (selection, index) => (
                  <Dropdown.Item
                    eventKey={index}
                    key={index}>
                      {selection}
                  </Dropdown.Item>
                )) : <></> }
              </EndpointDropdown>
            </Col>
            <Col>
            <StatusBox type="info" label="time">
                {liveXEndPoint.data.metadata?.time}
            </StatusBox>
        </Col>
        </Row>
        </Container>
        </TitleCard>
    )
}

export default Metadata;

