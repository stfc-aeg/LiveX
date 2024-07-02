import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container, Stack } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import Dropdown from 'react-bootstrap/Dropdown';
import Button from 'react-bootstrap/Button';
import { TitleCard, WithEndpoint, useAdapterEndpoint, ToggleSwitch, StatusBox, DropdownSelector } from 'odin-react';


const EndPointFormControl = WithEndpoint(Form.Control);
const EndpointButton = WithEndpoint(Button);

function Trigger() {

    const triggerEndPoint = useAdapterEndpoint('trigger', 'http://192.168.0.22:8888', 1000);

    return (
        <TitleCard title="metadata" type="warning">
        <Container>
        <Row>
          <Col>
          <StatusBox
            type="info"
            label="furnace enable">
              {triggerEndPoint?.data.enable?.furnace}
          </StatusBox>
          </Col>
          <Col>
          <StatusBox
            type="info"
            label="widefov enable">
              {triggerEndPoint?.data.enable?.wideFov}
          </StatusBox>
          </Col>
          <Col>
          <StatusBox
            type="info"
            label="narrowfov enable">
              {triggerEndPoint?.data.enable?.narrowFov}
          </StatusBox>
          </Col>
        </Row>
        <Row>
          <Col>
            <EndpointButton
              endpoint={triggerEndPoint}
              fullpath={"enable/furnace"}
              value={!triggerEndPoint?.data.enable?.furnace}
              event_type="click"
              >
                Toggle furnace: {triggerEndPoint?.data.enable?.furnace ? "Disable" : "Enable"}
            </EndpointButton>
          </Col>
          <Col>
            <EndpointButton
              endpoint={triggerEndPoint}
              fullpath={"enable/wideFov"}
              value={!triggerEndPoint?.data.enable?.wideFov}
              event_type="click"
              >
                Toggle wideFov: {triggerEndPoint?.data.enable?.wideFov ? "Disable" : "Enable"}
            </EndpointButton>
          </Col>
          <Col>
            <EndpointButton
              endpoint={triggerEndPoint}
              fullpath={"enable/narrowFov"}
              value={!triggerEndPoint?.data.enable?.narrowFov}
              event_type="click"
              >
                Toggle narrowFov: {triggerEndPoint?.data.enable?.  narrowFov ? "Disable" : "Enable"}
            </EndpointButton>
          </Col>
        </Row>
        <Row>
          <Col>
            <InputGroup>
              <InputGroup.Text>
                Furnace frequency
              </InputGroup.Text>
              <EndPointFormControl
                endpoint={triggerEndPoint}
                type="number"
                fullpath={"frequency/furnace"}
                value={triggerEndPoint.data.frequency?.furnace}>
              </EndPointFormControl>
            </InputGroup>
          </Col>
          <Col>
            <InputGroup>
              <InputGroup.Text>
                widefov frequency
              </InputGroup.Text>
              <EndPointFormControl
                endpoint={triggerEndPoint}
                type="number"
                fullpath={"frequency/wideFov"}
                value={triggerEndPoint.data.frequency?.wideFov}>
              </EndPointFormControl>
            </InputGroup>
          </Col>
          <Col>
            <InputGroup>
              <InputGroup.Text>
                narrowfov frequency
              </InputGroup.Text>
              <EndPointFormControl
                endpoint={triggerEndPoint}
                type="number"
                fullpath={"frequency/narrowFov"}
                value={triggerEndPoint.data.frequency?.narrowFov}>
              </EndPointFormControl>
            </InputGroup>
          </Col>
        </Row>


        </Container>
        </TitleCard>
    )
}

export default Trigger;

