import './App.css';

import 'odin-react/dist/index.css'
import 'bootstrap/dist/css/bootstrap.min.css';

import { checkNull } from './utils';

import React from "react";
import { TitleCard, ToggleSwitch, DropdownSelector, StatusBox, OdinApp } from 'odin-react';
import { WithEndpoint, useAdapterEndpoint } from 'odin-react';
import TemperatureGraph from './components/TemperatureGraph';
import PidControl from './components/PidControl';
import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';
import Dropdown from 'react-bootstrap/Dropdown';
import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';

const EndpointDropdown = WithEndpoint(DropdownSelector);
const EndPointToggle = WithEndpoint(ToggleSwitch);
const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function App(props) {

  const liveXEndPoint = useAdapterEndpoint('livex', 'http://localhost:8888', 1000);
  const graphEndPoint = useAdapterEndpoint('graph/thermocouples/data', 'http://localhost:8888', 1000);
  const graphAdapterEndPoint = useAdapterEndpoint('graph', 'http://localhost:8888', 0);
  // Disable if NOT connected or if putting. Workaround for odin-react not treating manual disable tags as OR
  const connectedPuttingDisable = (!(liveXEndPoint.data.status?.connected || false)) || (liveXEndPoint.loading == "putting")

  const motorDirections = ['Down', 'Up'];

  return (
    <OdinApp title="LiveX Controls" navLinks={["controls", "monitoring", "cameras"]}>
    <Col>
    <Container>
      <Col>
      <EndPointButton
        endpoint={liveXEndPoint}
        value={true}
        fullpath="status/reconnect"
        event_type="click"
        disabled={!connectedPuttingDisable}
        variant={liveXEndPoint.data.status?.connected ? "primary" : "danger"}>
        {liveXEndPoint.data.status?.connected ? 'Connected' : 'Reconnect'}
      </EndPointButton>

      <PidControl
        liveXEndPoint={liveXEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}
        title="Upper Heater (A) Controls"
        pid="pid_a">
      </PidControl>

      <PidControl
        liveXEndPoint={liveXEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}
        title="Lower Heater (B) Controls"
        pid="pid_b">
      </PidControl>

      <TitleCard title="test card">
        <Container>
          <Row>
          <EndPointButton
            endpoint={liveXEndPoint}
            fullpath={"tcp/acquire"}
            value={liveXEndPoint.data.tcp?.acquire ? false : true}
            event_type="click"
            disable={connectedPuttingDisable}
            variant={liveXEndPoint.data.tcp?.acquire ? "danger" : "success" }>
              {liveXEndPoint.data.tcp?.acquire ? "Stop acquisition" : "Start acquisition"}
          </EndPointButton>
          <Col>
          <Row>
            <StatusBox as="span" type="info" label="reading">
              {liveXEndPoint.data.tcp?.tcp_reading?.counter} {liveXEndPoint.data.tcp?.tcp_reading?.temperature_a}
            </StatusBox>
            </Row>
            </Col>
          </Row>
        </Container>

      </TitleCard>

      <TitleCard title="Thermal Gradient">
        <Container>
          <Row>
            <Col>
              <EndPointToggle 
                endpoint={liveXEndPoint}
                fullpath="gradient/enable"
                event_type="click"
                checked={liveXEndPoint.data.gradient?.enable || false} label="Enable" disabled={connectedPuttingDisable}>
              </EndPointToggle>
            </Col>
          </Row>
          <Row>
            <Col>
              <StatusBox
                type="info"
                label="Actual">
                  {checkNull(liveXEndPoint.data.gradient?.actual)}
                </StatusBox>
              <StatusBox
                type="info"
                label="Theoretical">
                  {checkNull(liveXEndPoint.data.gradient?.theoretical)}
              </StatusBox>
            </Col>
            <Col>
              <InputGroup>
                <InputGroup.Text>
                  Wanted (K/mm)
                </InputGroup.Text>
                <EndPointFormControl
                  endpoint={liveXEndPoint}
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
                  endpoint={liveXEndPoint}
                  type="number"
                  fullpath="gradient/distance"
                  disabled={connectedPuttingDisable}></EndPointFormControl>
              </InputGroup>
                High: 
              <EndpointDropdown
                endpoint={liveXEndPoint}
                event_type="select"
                fullpath="gradient/high_heater"
                buttonText={liveXEndPoint.data.gradient?.high_heater_options[liveXEndPoint.data.gradient.high_heater] || "Unknown"}
                disabled={connectedPuttingDisable}>
                  {liveXEndPoint.data.gradient?.high_heater_options ? liveXEndPoint.data.gradient.high_heater_options.map(
                  (selection, index) => (
                    <Dropdown.Item
                      eventKey={index}
                      key={index}>
                        {selection}
                    </Dropdown.Item>
                  )) : <></> }
              </EndpointDropdown>
            </Col>
          </Row>
        </Container>
      </TitleCard>

      <TitleCard title="Auto Set Point Control">
        <Container>
          <Row>
            <Col>
              <EndPointToggle endpoint={liveXEndPoint} fullpath="autosp/enable" event_type="click" 
                checked={liveXEndPoint.data.autosp?.enable || false} label="Enable" disabled={connectedPuttingDisable}>
              </EndPointToggle>
            </Col>
          </Row>
          <Row>
            <Col>
              <StatusBox
                type="info"
                label="Mid Pt. TEMP.">
                  {checkNull(liveXEndPoint.data.autosp?.midpt_temp)}
              </StatusBox>
            </Col>
            <Col>
              <EndpointDropdown
                endpoint={liveXEndPoint} event_type="select"
                fullpath="autosp/heating"
                buttonText={liveXEndPoint.data.autosp?.heating_options[liveXEndPoint.data.autosp.heating] || "Unknown"} disabled={connectedPuttingDisable}>
                {liveXEndPoint.data.autosp?.heating_options ? liveXEndPoint.data.autosp.heating_options.map(
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
                   Rate (K/s)
                </InputGroup.Text>
                <EndPointFormControl
                  endpoint={liveXEndPoint}
                  type="number"
                  fullpath="autosp/rate"
                  disabled={connectedPuttingDisable}>
                </EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
          <Row>
            <Col>
              <InputGroup>
                <InputGroup.Text>
                  Img Aquisition Per Degree (Img/K)
                </InputGroup.Text>
                <EndPointFormControl
                  endpoint={liveXEndPoint}
                  type="number"
                  fullpath="autosp/img_per_degree"
                  disabled={connectedPuttingDisable}>
                </EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
        </Container>
      </TitleCard>

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
      </Col>
    </Container>
    </Col>
    <Col>
    <TemperatureGraph
      graphEndPoint={graphEndPoint}
      graphAdapterEndPoint={graphAdapterEndPoint}
      connectedPuttingDisable={connectedPuttingDisable}>
    </TemperatureGraph>
    </Col>
    </OdinApp>
  );
}

export default App;