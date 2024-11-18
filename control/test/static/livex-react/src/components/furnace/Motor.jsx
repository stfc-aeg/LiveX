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
    const {furnaceEndPoint} = props;
    const {connectedPuttingDisable} = props;

    const motorDirections = ['Down', 'Up'];
    const labelWidth=80;

    return (
      <TitleCard title={
        <Row>
          <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Motor Controls</Col>
          <Col xs={3}>
            <EndPointToggle
              endpoint={furnaceEndPoint}
              fullpath="motor/enable"
              event_type="click"
              checked={furnaceEndPoint.data.motor?.enable || false}
              label="Enable"
              disabled={connectedPuttingDisable}>
            </EndPointToggle>
          </Col>
        </Row>
      }>
        <Row className="mt-3">
          <Col>
            <InputGroup>
              <InputGroup.Text>
                  Speed (0-4095)
              </InputGroup.Text>
              <EndPointFormControl
                endpoint={furnaceEndPoint}
                type="number"
                fullpath="motor/speed"
                event_type="enter"
                disabled={connectedPuttingDisable}>
              </EndPointFormControl>
            </InputGroup>
          </Col>
          <Col>
            <InputGroup>
              <InputGroup.Text>Motor direction:</InputGroup.Text>
              <EndpointDropdown
                endpoint={furnaceEndPoint}
                event_type="select"
                fullpath="motor/direction"
                variant="outline-secondary"
                buttonText={motorDirections[furnaceEndPoint.data.motor?.direction] || "Unknown"}
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
            </InputGroup>
          </Col>
          <Col>
            <InputGroup>
              <InputGroup.Text style={{width: labelWidth}}>
                LVDT (mm)
              </InputGroup.Text>
              <InputGroup.Text style={{
                width: labelWidth,
                border: '1px solid lightblue',
                backgroundColor: '#e0f7ff'
                }}>
                {checkNull(furnaceEndPoint.data.motor?.lvdt)}
              </InputGroup.Text>
            </InputGroup>
          </Col>
        </Row>
      </TitleCard>
    )
}
export default Motor;