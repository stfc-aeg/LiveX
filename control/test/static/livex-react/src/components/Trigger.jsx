import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import { TitleCard, WithEndpoint, useAdapterEndpoint, StatusBox } from 'odin-react';

import { checkNullNoDp } from '../utils';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndpointButton = WithEndpoint(Button);

function Trigger() {

    const triggerEndPoint = useAdapterEndpoint('trigger', 'http://192.168.0.22:8888', 1000);

    const orcaEndPoint = useAdapterEndpoint('camera/cameras/0', 'http://192.168.0.22:8888', 1000);
    const liveXEndPoint = useAdapterEndpoint('furnace', 'http://192.168.0.22:8888', 1000);

    const acqEndPoint = useAdapterEndpoint('livex', 'http://192.168.0.22:8888', 1000);

    return (
        <TitleCard title="trigger toggles" type="warning">
        <Container>
        <Row>
          <Col>
          <StatusBox
            type="info"
            label="furnace enable">
              {triggerEndPoint?.data.furnace?.enable}
          </StatusBox>
          </Col>
          <Col>
          <StatusBox
            type="info"
            label="widefov enable">
              {triggerEndPoint?.data.widefov?.enable}
          </StatusBox>
          </Col>
          <Col>
          <StatusBox
            type="info"
            label="narrowfov enable">
              {triggerEndPoint?.data.narrowfov?.enable}
          </StatusBox>
          </Col>
        </Row>
        <Row>
          <Col>
            <EndpointButton
              endpoint={triggerEndPoint}
              fullpath={"furnace/enable"}
              value={!triggerEndPoint?.data.furnace?.enable}
              event_type="click"
              >
                Toggle furnace: {triggerEndPoint?.data.furnace?.enable ? "Disable" : "Enable"}
            </EndpointButton>
          </Col>
          <Col>
            <EndpointButton
              endpoint={triggerEndPoint}
              fullpath={"widefov/enable"}
              value={!triggerEndPoint?.data.widefov?.enable}
              event_type="click"
              >
                Toggle widefov: {triggerEndPoint?.data.widefov?.enable ? "Disable" : "Enable"}
            </EndpointButton>
          </Col>
          <Col>
            <EndpointButton
              endpoint={triggerEndPoint}
              fullpath={"narrowfov/enable"}
              value={!triggerEndPoint?.data.narrowfov?.enable}
              event_type="click"
              >
                Toggle narrowfov: {triggerEndPoint?.data.narrowfov?.enable ? "Disable" : "Enable"}
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
                fullpath={"furnace/frequency"}
                value={triggerEndPoint.data.furnace?.frequency}>
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
                fullpath={"widefov/frequency"}
                value={triggerEndPoint.data.narrowfov?.frequency}>
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
                fullpath={"narrowfov/frequency"}
                value={triggerEndPoint.data.narrowfov?.frequency}>
              </EndPointFormControl>
            </InputGroup>
          </Col>
        </Row>
        <Row>
          <Col>
            <InputGroup>
              <InputGroup.Text>
                Furnace frame target
              </InputGroup.Text>
              <EndPointFormControl
                endpoint={triggerEndPoint}
                type="number"
                fullpath={"furnace/target"}
                value={triggerEndPoint.data.furnace?.target}>
              </EndPointFormControl>
            </InputGroup>
          </Col>
          <Col>
            <InputGroup>
              <InputGroup.Text>
                widefov frame target
              </InputGroup.Text>
              <EndPointFormControl
                endpoint={triggerEndPoint}
                type="number"
                fullpath={"widefov/target"}
                value={triggerEndPoint.data.narrowfov?.target}>
              </EndPointFormControl>
            </InputGroup>
          </Col>
          <Col>
            <InputGroup>
              <InputGroup.Text>
                narrowfov frame target
              </InputGroup.Text>
              <EndPointFormControl
                endpoint={triggerEndPoint}
                type="number"
                fullpath={"narrowfov/target"}
                value={triggerEndPoint.data.narrowfov?.target}>
              </EndPointFormControl>
            </InputGroup>
          </Col>
        </Row>

        <Row className='mt-3'>

        <Col>
          <StatusBox as="span" label="reading">
                {checkNullNoDp(liveXEndPoint.data.tcp?.tcp_reading?.counter)}
          </StatusBox>
        </Col>
        <Col>
          <StatusBox label="Frame count">
            {checkNullNoDp(orcaEndPoint?.data[0]?.status.frame_number)}
          </StatusBox>
        </Col>

        </Row>

        <Row>
          <EndpointButton
            endpoint={acqEndPoint}
            fullpath={"acquisition/start"}
            value={true}
            event_type="click"
            >
              start acquisition: {acqEndPoint?.data?.server_uptime}
          </EndpointButton>
        </Row>
        <Row>
          <EndpointButton
            endpoint={acqEndPoint}
            fullpath={"acquisition/stop"}
            value={true}
            event_type="click"
            variant="danger"
            >
              stop acquisition: {acqEndPoint?.data?.server_uptime}
          </EndpointButton>
        </Row>


        </Container>
        </TitleCard>
    )
}

export default Trigger;

