import React from 'react';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import { TitleCard, WithEndpoint, ToggleSwitch } from 'odin-react';
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
      <TitleCard
        title={
          <Row>
            <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>{title}</Col>
            <Col xs={3}>
              <EndPointToggle
                endpoint={furnaceEndPoint}
                fullpath={pid+"/enable"}
                event_type="click"
                checked={furnaceEndPoint.data[pid]?.enable || false}
                label="Enable"
                disabled={connectedPuttingDisable}>
              </EndPointToggle>
            </Col>
          </Row>
        }>
        <Row>
          <Col xs={6} sm={12}>
            <Row>
              <Col xs={12} sm={6}>
                <Row>
                  <InputGroup>
                    <InputGroup.Text style={{width:pidLabelWidth}}>
                      Proportional
                    </InputGroup.Text>
                    <EndPointFormControl
                      endpoint={furnaceEndPoint}
                      type="number"
                      fullpath={pid+"/proportional"}
                      event_type="enter"
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
                      event_type="enter"
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
                      event_type="enter"
                      disabled={connectedPuttingDisable}>
                    </EndPointFormControl>
                  </InputGroup>
                </Row>
              </Col>
              <Col xs={12} sm={6}>
                <Row>
                  <InputGroup>
                    <InputGroup.Text style={{width:labelWidth}}>
                      Set Pt. In
                    </InputGroup.Text>
                    <EndPointFormControl
                      endpoint={furnaceEndPoint}
                      type="number"
                      fullpath={pid+"/setpoint"}
                      event_type="enter"
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
                    {checkNull(furnaceEndPoint.data[pid]?.setpoint)}
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
                        {checkNull((furnaceEndPoint.data[pid]?.temperature))}
                    </InputGroup.Text>
                  </InputGroup>
              </Row>
              </Col>
            </Row>
          </Col>
        </Row>
      </TitleCard>
    )
}

export default PidControl;