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
    const {furnaceEndPoint} = props;
    const {connectedPuttingDisable} = props;
    const {title} = props;
    const {pid} = props;

    // Fixing the label width of the display labels so that they're consistent
    // ~6px per character. 
    const labelWidth = 64;
    const pidLabelWidth = 72;

    return (
      <TitleCard title={title} type="warning">
        <Row>
          <Col xs={6} sm={8} md={8} lg={8} xl={8} xxl={8}>
            <Row>
              <EndPointToggle 
                endpoint={furnaceEndPoint}
                fullpath={pid+"/enable"}
                event_type="click"
                checked={furnaceEndPoint.data[pid]?.enable || false}
                label="Enable"
                disabled={connectedPuttingDisable}>
              </EndPointToggle>
            </Row>
            <Row className="mt-4">
              <Col xs={12} md={6}>
                <InputGroup>
                  <InputGroup.Text style={{width:pidLabelWidth}}>
                    Proportional
                  </InputGroup.Text>
                  <EndPointFormControl
                    endpoint={furnaceEndPoint}
                    type="number"
                    fullpath={pid+"/proportional"}
                    disabled={connectedPuttingDisable}>
                  </EndPointFormControl>
                </InputGroup>
                <InputGroup>
                  <InputGroup.Text style={{width:pidLabelWidth}}>
                    Integral
                  </InputGroup.Text>
                  <EndPointFormControl
                    endpoint={furnaceEndPoint}
                    type="number"
                    fullpath={pid+"/integral"}
                    disabled={connectedPuttingDisable}>
                  </EndPointFormControl>
                </InputGroup>
                <InputGroup>
                  <InputGroup.Text style={{width:pidLabelWidth}}>
                    Derivative
                  </InputGroup.Text>
                  <EndPointFormControl
                    endpoint={furnaceEndPoint}
                    type="number"
                    fullpath={pid+"/derivative"}
                    disabled={connectedPuttingDisable}>
                  </EndPointFormControl>
                </InputGroup>
              </Col>
              <Col xs={12} md={6}>
                <Row>
                  <Stack>
                  <InputGroup>
                    <InputGroup.Text style={{width:labelWidth}}>
                      Set Pt. In
                    </InputGroup.Text>
                    <EndPointFormControl
                      endpoint={furnaceEndPoint}
                      type="number"
                      fullpath={pid+"/setpoint"}
                      disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                  </InputGroup>
                  <InputGroup>
                    <InputGroup.Text style={{width: labelWidth}}>
                      Set Pt Out
                    </InputGroup.Text>
                    <InputGroup.Text style={{
                      width: labelWidth,
                      border: '1px solid lightblue',
                      backgroundColor: '#e0f7ff'
                    }}>
                    {
                      (furnaceEndPoint.data.gradient?.enable ||false) ?
                      checkNull(furnaceEndPoint.data[pid]?.gradient_setpoint) :
                      checkNull(furnaceEndPoint.data[pid]?.setpoint)
                    }
                    </InputGroup.Text>
                  </InputGroup>
                  </Stack>
                </Row>
              </Col>

            </Row>
          </Col>
          <Col xs={4}>
            <Row>
                <InputGroup>
                  <InputGroup.Text style={{width:labelWidth}}>
                    PID out.:
                  </InputGroup.Text>
                  <InputGroup.Text
                    style={{
                      width: labelWidth,
                      border: '1px solid lightblue',
                      backgroundColor: '#e0f7ff'
                    }}>
                      {checkNull(furnaceEndPoint.data[pid]?.output)}
                  </InputGroup.Text>
                </InputGroup>
              </Row>
            <Row>
              <InputGroup>
                <InputGroup.Text style={{width:labelWidth}}>
                  Volt out.:
                </InputGroup.Text>
                <InputGroup.Text
                  style={{
                    width: labelWidth,
                    border: '1px solid lightblue',
                    backgroundColor: '#e0f7ff'
                  }}>
                    {checkNull((furnaceEndPoint.data[pid]?.output) * 10 * 0.8)}
                </InputGroup.Text>
              </InputGroup>
            </Row>
            <Row>
              <InputGroup>
                <InputGroup.Text style={{width:labelWidth}}>
                  Temp.:
                </InputGroup.Text>
                <InputGroup.Text
                  style={{
                    width: labelWidth,
                    border: '1px solid lightblue',
                    backgroundColor: '#e0f7ff'
                  }}>
                    {checkNull((furnaceEndPoint.data[pid]?.output) * 10 * 0.8)}
                </InputGroup.Text>
              </InputGroup>
            </Row>
          </Col>
        </Row>
      </TitleCard>
    )
}

export default PidControl;