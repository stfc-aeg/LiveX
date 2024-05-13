import React from 'react';

import { checkNull } from '../../utils';

import { TitleCard, ToggleSwitch, DropdownSelector, StatusBox, WithEndpoint } from 'odin-react';
import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';
import Dropdown from 'react-bootstrap/Dropdown';
import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';

const EndpointDropdown = WithEndpoint(DropdownSelector);
const EndPointToggle = WithEndpoint(ToggleSwitch);
const EndPointFormControl = WithEndpoint(Form.Control);

function Motor(props){
    const {liveXEndPoint} = props;
    const {connectedPuttingDisable} = props;

    const motorDirections = ['Down', 'Up'];

    return (
      <TitleCard title="Motor Controls">
        <Container>
          <Row>
            <Col>
              <EndPointToggle
                endpoint={liveXEndPoint}
                fullpath="motor/enable"
                event_type="click"
                checked={liveXEndPoint.data.motor?.enable || false}
                label="Enable"
                disabled={connectedPuttingDisable}>
              </EndPointToggle>
            </Col>
          </Row>
          <Row>
            <Col>
              <StatusBox
              type="info"
              label="LVDT (mm)">
                {checkNull(liveXEndPoint.data.motor?.lvdt)}
              </StatusBox>
            </Col>
            <Col>
              <EndpointDropdown
                endpoint={liveXEndPoint}
                event_type="select"
                fullpath="motor/direction"
                buttonText={motorDirections[liveXEndPoint.data.motor?.direction] || "Unknown"}
                disabled={connectedPuttingDisable}>
                  {motorDirections ? motorDirections.map(
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
              <InputGroup>
                <InputGroup.Text>
                   Speed (0-4095)
                </InputGroup.Text>
                <EndPointFormControl
                  endpoint={liveXEndPoint}
                  type="number"
                  fullpath="motor/speed"
                  disabled={connectedPuttingDisable}>
                </EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
        </Container>
      </TitleCard>
    )
}
export default Motor;