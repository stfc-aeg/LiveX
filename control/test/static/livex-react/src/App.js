import './App.css';

import 'odin-react/dist/index.css'

import 'bootstrap/dist/css/bootstrap.min.css';

import React, { useState } from "react";
import {TitleCard, ToggleSwitch, DropdownSelector, StatusBox, OdinApp} from 'odin-react';
import {WithEndpoint, useAdapterEndpoint} from 'odin-react';
import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';
import Dropdown from 'react-bootstrap/Dropdown';
import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Stack from 'react-bootstrap/Stack';

const EndpointDropdown = WithEndpoint(DropdownSelector);
const EndPointToggle = WithEndpoint(ToggleSwitch);
const EndPointFormControl = WithEndpoint(Form.Control);

function App(props) {

  const liveXEndPoint = useAdapterEndpoint('livex', 'http://localhost:8888', 1000);

  return (
    <OdinApp title="LiveX Controls" navLinks={["controls", "monitoring", "cameras"]}>
    <Container>
      <TitleCard title="Upper Heater (A) Controls">
      <Container>
        <Row>
          <Col xs={8}>
            <EndPointToggle endpoint={liveXEndPoint} fullpath="pid_a/enable" event_type="click"
            checked={liveXEndPoint.data.pid_a?.enable || false} label="Enable">
            </EndPointToggle>
          </Col>
          <Col>
            <StatusBox type="info" label="PID OUT.">{(liveXEndPoint.data.pid_a?.output || -1).toFixed(2)}
            </StatusBox>
          </Col>

        </Row>
        <Row>
          <Col xs={4}>
            <InputGroup>
              <InputGroup.Text>Proportional</InputGroup.Text>
              <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_a/proportional"></EndPointFormControl>
            </InputGroup>

            <InputGroup>
              <InputGroup.Text>Integral</InputGroup.Text>
              <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_a/integral"></EndPointFormControl>
            </InputGroup>

            <InputGroup>
              <InputGroup.Text>Derivative</InputGroup.Text>
              <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_a/derivative"></EndPointFormControl>
            </InputGroup>
          </Col>
          <Col>
            <Row>
              <Stack>
                <InputGroup>
                  <InputGroup.Text>Set Pt.</InputGroup.Text>
                  <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_a/setpoint"></EndPointFormControl>
                </InputGroup>
                <StatusBox as="span" type="info" label="Setpoint">
                {(liveXEndPoint.data.gradient?.enable || false) ?
                  liveXEndPoint.data.pid_a.setpoint - (liveXEndPoint.data.gradient?.modifier || 0)
                : liveXEndPoint.data.pid_a?.setpoint || -1}
                </StatusBox>
              </Stack>
            </Row>
          </Col>
          <Col>
            <StatusBox type="info" label="TEMP.">{liveXEndPoint.data.pid_a?.temperature || -1}
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
                checked={liveXEndPoint.data.pid_b?.enable || false} label="Enable">
              </EndPointToggle>
            </Col>
            <Col>
              <StatusBox type="info" label="PID OUT.">{(liveXEndPoint.data.pid_b?.output || -1).toFixed(2)}
              </StatusBox>
            </Col>
          </Row>
          <Row>
            <Col xs={4}>
              <InputGroup>
                <InputGroup.Text>Proportional Term</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_b/proportional"></EndPointFormControl>
              </InputGroup>

              <InputGroup>
                <InputGroup.Text>Integral Term</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_b/integral"></EndPointFormControl>
              </InputGroup>

              <InputGroup>
                <InputGroup.Text>Derivative Term</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_b/derivative"></EndPointFormControl>
              </InputGroup>
            </Col>
            <Col>
              <InputGroup>
                <InputGroup.Text>Set Pt.</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="pid_b/setpoint"></EndPointFormControl>
              </InputGroup>
              <StatusBox type="info" label="Setpoint">
              {(liveXEndPoint.data.gradient?.enable || false) ?
                  liveXEndPoint.data.pid_b.setpoint - (liveXEndPoint.data.gradient?.modifier || 0)
                : liveXEndPoint.data.pid_b?.setpoint || -1}
              </StatusBox>
            </Col>
            <Col>
              <StatusBox type="info" label="TEMP.">{liveXEndPoint.data.pid_b?.temperature || -1}
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
          checked={liveXEndPoint.data.gradient?.enable || false} label="Enable"></EndPointToggle>
            </Col>
          </Row>
          <Row>
            <Col>
              <StatusBox type="info" label="Actual">{liveXEndPoint.data.gradient?.actual || -1}</StatusBox>
              <StatusBox type="info" label="Theoretical">{liveXEndPoint.data.gradient?.theoretical || -1}</StatusBox>
            </Col>
            <Col>
              <InputGroup>
                <InputGroup.Text>Wanted (K/mm)</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="gradient/wanted"></EndPointFormControl>
              </InputGroup>
        
              <InputGroup>
                <InputGroup.Text>Distance (mm)</InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="gradient/distance"></EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
        </Container>
      </TitleCard>

      <TitleCard title="Auto Set Point Control">
        <Container>
          <Row>
            <Col>
              <EndPointToggle endpoint={liveXEndPoint} fullpath="autosp/enable" event_type="click" 
                checked={liveXEndPoint.data.autosp?.enable || false} label="Enable">
              </EndPointToggle>
            </Col>
          </Row>
          <Row>
            <Col>
              <StatusBox type="info" label="Mid Pt. TEMP.">{liveXEndPoint.data.autosp?.midpt_temp || -1}
              </StatusBox>
            </Col>
            <Col>
              <EndpointDropdown endpoint={liveXEndPoint} event_type="select" fullpath="autosp/heating" buttonText={liveXEndPoint.data.autosp?.heating_options[liveXEndPoint.data.autosp.heating] || "Unknown"}>
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
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="autosp/rate"></EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
          <Row>
            <Col>
              <InputGroup>
                <InputGroup.Text>
                  Img Aquisition Per Degree (Img/K)
                </InputGroup.Text>
                <EndPointFormControl endpoint={liveXEndPoint} type="number" fullpath="autosp/img_per_degree"></EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
        </Container>

      </TitleCard>
    </Container>
    </OdinApp>
  );
}

export default App;
