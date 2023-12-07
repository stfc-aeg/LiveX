import './App.css';

import 'odin-react/dist/index.css'

import 'bootstrap/dist/css/bootstrap.min.css';

import React, { useState } from "react";
import { TitleCard, ToggleSwitch, DropdownSelector, StatusBox, OdinApp, OdinGraph } from 'odin-react';
import { WithEndpoint, useAdapterEndpoint } from 'odin-react';
import TemperatureGraph from './components/TemperatureGraph';
import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';
import Dropdown from 'react-bootstrap/Dropdown';
import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Stack from 'react-bootstrap/Stack';
import Button from 'react-bootstrap/Button';

const EndpointDropdown = WithEndpoint(DropdownSelector);
const EndPointToggle = WithEndpoint(ToggleSwitch);
const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function App(props) {

  const liveXEndPoint = useAdapterEndpoint('livex', 'http://localhost:8888', 100);
  // Disable if NOT connected or if putting. Workaround for odin-react not treating manual disable tags as OR
  const connectedPuttingDisable = (!(liveXEndPoint.data.status?.connected || false)) || (liveXEndPoint.loading == "putting")

  const motorDirections = ['Down', 'Up'];

  return (
    <OdinApp title="LiveX Controls" navLinks={["controls", "monitoring", "cameras"]}>
    <Col>
    <Container>
      <Col>
      <EndPointButton endpoint={liveXEndPoint} value={true} fullpath="status/reconnect" event_type="click" 
      disabled={!connectedPuttingDisable}>
        {liveXEndPoint.data.status?.connected ? 'Connected' : 'Reconnect'}
      </EndPointButton>

      <TitleCard title="Upper Heater (A) Controls" type="warning">
      <Container>
        <Row>
          <Col xs={8}>
            <EndPointToggle endpoint={liveXEndPoint} fullpath="pid_a/enable" event_type="click"
            checked={liveXEndPoint.data.pid_a?.enable || false} label="Enable" disabled={connectedPuttingDisable}>
            </EndPointToggle>
          </Col>
          <Col>
            <StatusBox type="info" label="PID OUT.">{(liveXEndPoint.data.pid_a?.output || 0).toFixed(2)}
            </StatusBox>
          </Col>

        </Row>
        <Row>
          <Col xs={4}>
            <InputGroup>
              <InputGroup.Text>Proportional</InputGroup.Text>
              <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_a/proportional" disabled={connectedPuttingDisable}></EndPointFormControl>
            </InputGroup>

            <InputGroup>
              <InputGroup.Text>Integral</InputGroup.Text>
              <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_a/integral" disabled={connectedPuttingDisable}></EndPointFormControl>
            </InputGroup>

            <InputGroup>
              <InputGroup.Text>Derivative</InputGroup.Text>
              <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_a/derivative" disabled={connectedPuttingDisable}></EndPointFormControl>
            </InputGroup>
          </Col>
          <Col>
            <Row>
              <Stack>
                <InputGroup>
                  <InputGroup.Text>Set Pt.</InputGroup.Text>
                  <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_a/setpoint" disabled={connectedPuttingDisable}></EndPointFormControl>
                </InputGroup>
                <StatusBox as="span" type="info" label="Setpoint">
                {(liveXEndPoint.data.gradient?.enable ||
                  false) ?
                  liveXEndPoint.data.pid_a?.gradient_setpoint || -2 :
                  liveXEndPoint.data.pid_a?.setpoint || 0
                }
                </StatusBox>
              </Stack>
            </Row>
          </Col>
          <Col>
            <StatusBox type="info" label="TEMP.">{liveXEndPoint.data.pid_a?.temperature || 0}
            </StatusBox>
          </Col>
        </Row>
      
        </Container>
      </TitleCard>

      <TitleCard title="Lower Heater (B) Controls">
        <Container>
          <Row>
            <Col xs={8}>
              <EndPointToggle endpoint={liveXEndPoint} fullpath="pid_b/enable" event_type="click"
                checked={liveXEndPoint.data.pid_b?.enable || false} label="Enable" disabled={connectedPuttingDisable}>
              </EndPointToggle>
            </Col>
            <Col>
              <StatusBox type="info" label="PID OUT.">{(liveXEndPoint.data.pid_b?.output || 0).toFixed(2)}
              </StatusBox>
            </Col>
          </Row>
          <Row>
            <Col xs={4}>
              <InputGroup>
                <InputGroup.Text>Proportional Term</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_b/proportional" disabled={connectedPuttingDisable}></EndPointFormControl>
              </InputGroup>

              <InputGroup>
                <InputGroup.Text>Integral Term</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_b/integral" disabled={connectedPuttingDisable}></EndPointFormControl>
              </InputGroup>

              <InputGroup>
                <InputGroup.Text>Derivative Term</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_b/derivative" disabled={connectedPuttingDisable}></EndPointFormControl>
              </InputGroup>
            </Col>
            <Col>
              <InputGroup>
                <InputGroup.Text>Set Pt.</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_b/setpoint" disabled={connectedPuttingDisable}></EndPointFormControl>
              </InputGroup>
              <StatusBox type="info" label="Setpoint">
              {(liveXEndPoint.data.gradient?.enable ||
                  false) ?
                  liveXEndPoint.data.pid_b?.gradient_setpoint || -2 :
                  liveXEndPoint.data.pid_b?.setpoint || 0
                }
              </StatusBox>
            </Col>
            <Col>
              <StatusBox type="info" label="TEMP.">{liveXEndPoint.data.pid_b?.temperature || 0}
              </StatusBox>
            </Col>
          </Row>
        </Container>
      </TitleCard>

      <TitleCard title="Thermal Gradient">
        <Container>
          <Row>
            <Col>
              <EndPointToggle endpoint={liveXEndPoint} fullpath="gradient/enable" event_type="click"
          checked={liveXEndPoint.data.gradient?.enable || false} label="Enable" disabled={connectedPuttingDisable}></EndPointToggle>
            </Col>
          </Row>
          <Row>
            <Col>
              <StatusBox type="info" label="Actual">{liveXEndPoint.data.gradient?.actual || 0}</StatusBox>
              <StatusBox type="info" label="Theoretical">{liveXEndPoint.data.gradient?.theoretical || 0}</StatusBox>
            </Col>
            <Col>
              <InputGroup>
                <InputGroup.Text>Wanted (K/mm)</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="gradient/wanted" disabled={connectedPuttingDisable}></EndPointFormControl>
              </InputGroup>
        
              <InputGroup>
                <InputGroup.Text>Distance (mm)</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="gradient/distance" disabled={connectedPuttingDisable}></EndPointFormControl>
              </InputGroup>
              High: 
              <EndpointDropdown endpoint={liveXEndPoint} event_type="select" fullpath="gradient/high_heater" buttonText={liveXEndPoint.data.gradient?.high_heater_options[liveXEndPoint.data.gradient.high_heater] || "Unknown"} disabled={connectedPuttingDisable}>
              {liveXEndPoint.data.gradient?.high_heater_options ? liveXEndPoint.data.gradient.high_heater_options.map(
              (selection, index) => (
              <Dropdown.Item eventKey={index} key={index}>{selection}</Dropdown.Item>
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
              <StatusBox type="info" label="Mid Pt. TEMP.">{liveXEndPoint.data.autosp?.midpt_temp || 0}
              </StatusBox>
            </Col>
            <Col>
              <EndpointDropdown endpoint={liveXEndPoint} event_type="select" fullpath="autosp/heating" buttonText={liveXEndPoint.data.autosp?.heating_options[liveXEndPoint.data.autosp.heating] || "Unknown"} disabled={connectedPuttingDisable}>
              {liveXEndPoint.data.autosp?.heating_options ? liveXEndPoint.data.autosp.heating_options.map(
              (selection, index) => (
              <Dropdown.Item eventKey={index} key={index}>{selection}</Dropdown.Item>
              )) : <></> }
              </EndpointDropdown>
            </Col>
            <Col>
              <InputGroup>
                <InputGroup.Text>
                   Rate (K/s)
                </InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="autosp/rate" disabled={connectedPuttingDisable}></EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
          <Row>
            <Col>
              <InputGroup>
                <InputGroup.Text>
                  Img Aquisition Per Degree (Img/K)
                </InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="autosp/img_per_degree" disabled={connectedPuttingDisable}></EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
        </Container>
      </TitleCard>


      <TitleCard title="Motor Controls">
        <Container>
          <Row>
            <Col>
              <EndPointToggle endpoint={liveXEndPoint} fullpath="motor/enable" event_type="click" 
                checked={liveXEndPoint.data.motor?.enable || false} label="Enable" disabled={connectedPuttingDisable}>
              </EndPointToggle>
            </Col>
          </Row>
          <Row>
            <Col>
              <StatusBox type="info" label="LVDT (mm)">{liveXEndPoint.data.motor?.lvdt || 0}
              </StatusBox>
            </Col>
            <Col>
              <EndpointDropdown endpoint={liveXEndPoint} event_type="select" fullpath="motor/direction" buttonText={motorDirections[liveXEndPoint.data.motor?.direction] || "Unknown"} disabled={connectedPuttingDisable}>
              {motorDirections ? motorDirections.map(
              (selection, index) => (
              <Dropdown.Item eventKey={index} key={index}>{selection}</Dropdown.Item>
              )) : <></> }
              </EndpointDropdown>
            </Col>
            <Col>
              <InputGroup>
                <InputGroup.Text>
                   Speed (Volts?)
                </InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="motor/speed" disabled={connectedPuttingDisable}></EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
        </Container>
      </TitleCard>
      </Col>
    </Container>
    </Col>
    <Col>
    <TemperatureGraph liveXEndPoint={liveXEndPoint}></TemperatureGraph>
    </Col>
    </OdinApp>
  );
}

export default App;
