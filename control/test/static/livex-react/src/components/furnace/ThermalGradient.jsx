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

function ThermalGradient(props){
    const {furnaceEndPoint} = props;
    const {connectedPuttingDisable} = props;

    const labelWidth=128;
    const inputLabelWidth=96;

    return (
      <TitleCard title={
        <Row>
          <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Thermal Gradient</Col>
          <Col xs={3}>
            <EndPointToggle 
              endpoint={furnaceEndPoint}
              fullpath="gradient/enable"
              event_type="click"
              checked={furnaceEndPoint.data.gradient?.enable || false} label="Enable" disabled={connectedPuttingDisable}>
            </EndPointToggle>
          </Col>
        </Row>
      }>

        <Row>
          <Col>
          <InputGroup>
            <InputGroup.Text style={{width: inputLabelWidth}}>
              Wanted (K/mm)
            </InputGroup.Text>
            <EndPointFormControl
              endpoint={furnaceEndPoint}
              type="number"
              fullpath="gradient/wanted"
              disabled={connectedPuttingDisable}>
            </EndPointFormControl>
          </InputGroup>
          <InputGroup>
            <InputGroup.Text style={{width: inputLabelWidth}}>
              Distance (mm)
            </InputGroup.Text>
            <EndPointFormControl
              endpoint={furnaceEndPoint}
              type="number"
              fullpath="gradient/distance"
              disabled={connectedPuttingDisable}>
            </EndPointFormControl>
          </InputGroup>
          <InputGroup>
            <InputGroup.Text>
              Gradient high towards heater:
            </InputGroup.Text>
            <EndpointDropdown
              endpoint={furnaceEndPoint}
              event_type="select"
              fullpath="gradient/high_heater"
              variant="outline-secondary"
              buttonText={furnaceEndPoint.data.gradient?.high_heater_options[furnaceEndPoint.data.gradient.high_heater] || "Unknown"}
              disabled={connectedPuttingDisable}>
                {furnaceEndPoint.data.gradient?.high_heater_options ? furnaceEndPoint.data.gradient.high_heater_options.map(
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
                Actual
              </InputGroup.Text>
              <InputGroup.Text style={{
                width: labelWidth,
                border: '1px solid lightblue',
                backgroundColor: '#e0f7ff'
              }}>
                {checkNull(furnaceEndPoint.data.gradient?.actual)}
              </InputGroup.Text>
            </InputGroup>
            <InputGroup>
              <InputGroup.Text style={{width: labelWidth}}>
                Theoretical
              </InputGroup.Text>
              <InputGroup.Text style={{
                width: labelWidth,
                border: '1px solid lightblue',
                backgroundColor: '#e0f7ff'
              }}>
                {checkNull(furnaceEndPoint.data.gradient?.theoretical)}
              </InputGroup.Text>
            </InputGroup>
            <InputGroup>
              <InputGroup.Text style={{width: labelWidth}}>
                Centre Thermocouple
              </InputGroup.Text>
              <InputGroup.Text style={{
                width: labelWidth,
                border: '1px solid lightblue',
                backgroundColor: '#e0f7ff'
              }}>
                {checkNull(furnaceEndPoint.data.thermocouples?.centre)}
              </InputGroup.Text>
            </InputGroup>
          </Col>
        </Row>
      </TitleCard>
    )
}

export default ThermalGradient;
