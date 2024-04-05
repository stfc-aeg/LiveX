import React from 'react';

import { checkNull } from '../utils';

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
    const {liveXEndPoint} = props;
    const {connectedPuttingDisable} = props;

    return (
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
    )
}

export default ThermalGradient;
