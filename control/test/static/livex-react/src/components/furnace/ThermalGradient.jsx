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

    return (
        <TitleCard title="Thermal Gradient">
        <Container>
        <Row>
          <Col>
            <EndPointToggle 
              endpoint={furnaceEndPoint}
              fullpath="gradient/enable"
              event_type="click"
              checked={furnaceEndPoint.data.gradient?.enable || false} label="Enable" disabled={connectedPuttingDisable}>
            </EndPointToggle>
          </Col>
        </Row>
        <Row>
          <Col>
            <StatusBox
              type="info"
              label="Actual">
                {checkNull(furnaceEndPoint.data.gradient?.actual)}
            </StatusBox>
          <StatusBox
            type="info"
            label="Theoretical">
              {checkNull(furnaceEndPoint.data.gradient?.theoretical)}
          </StatusBox>
          <StatusBox
            type="info"
            label="Centre Thermocouple">
              {checkNull(furnaceEndPoint.data.thermocouples?.centre)}
          </StatusBox>
          </Col>
          <Col>
          <InputGroup>
            <InputGroup.Text>
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
            <InputGroup.Text>
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
        </Row>
        </Container>
    </TitleCard>
    )
}

export default ThermalGradient;
