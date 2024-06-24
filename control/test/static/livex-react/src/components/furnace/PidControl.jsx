import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container, Stack } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import { TitleCard, WithEndpoint, ToggleSwitch, StatusBox } from 'odin-react';

import { checkNull  } from '../../utils';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointToggle = WithEndpoint(ToggleSwitch);

function PidControl(props) {
    const {liveXEndPoint} = props;
    const {connectedPuttingDisable} = props;
    const {title} = props;
    const {pid} = props;

    return (
      <TitleCard title={title} type="warning">
        <Container>
        <Row>
            <Col xs={8}>
            <EndPointToggle 
                endpoint={liveXEndPoint}
                fullpath={pid+"/enable"}
                event_type="click"
                checked={liveXEndPoint.data[pid]?.enable || false}
                label="Enable"
                disabled={connectedPuttingDisable}>
            </EndPointToggle>
            </Col>
            <Col>
            <StatusBox
                type="info"
                label="PID OUT.">
                    {checkNull(liveXEndPoint.data[pid]?.output)}
            </StatusBox>
            </Col>

        </Row>
        <Row>
            <Col xs={4}>
            <InputGroup>
                <InputGroup.Text>
                    Proportional
                </InputGroup.Text>
                <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={pid+"/proportional"}
                    disabled={connectedPuttingDisable}>
                </EndPointFormControl>
            </InputGroup>
            <InputGroup>
                <InputGroup.Text>
                    Integral
                </InputGroup.Text>
                <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={pid+"/integral"}
                    disabled={connectedPuttingDisable}>
                </EndPointFormControl>
            </InputGroup>
            <InputGroup>
                <InputGroup.Text>
                    Derivative
                </InputGroup.Text>
                <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={pid+"/derivative"}
                    disabled={connectedPuttingDisable}>
                </EndPointFormControl>
            </InputGroup>
            </Col>
            <Col>
            <Row>
                <Stack>
                <InputGroup>
                    <InputGroup.Text>
                        Set Pt.
                    </InputGroup.Text>
                    <EndPointFormControl
                        endpoint={liveXEndPoint}
                        type="number"
                        fullpath={pid+"/setpoint"}
                        disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                </InputGroup>
                <StatusBox as="span" type="info"
                label="Setpoint">
                {(liveXEndPoint.data.gradient?.enable ||false) ?
                    checkNull(liveXEndPoint.data[pid]?.gradient_setpoint) :
                    checkNull(liveXEndPoint.data[pid]?.setpoint)
                }
                </StatusBox>
                </Stack>
            </Row>
            </Col>
            <Col>
            <StatusBox type="info" label="TEMP.">
                {checkNull(liveXEndPoint.data[pid]?.temperature)}
            </StatusBox>
            </Col>
        </Row>
        </Container>
      </TitleCard>
    )
}

export default PidControl;